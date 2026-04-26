use std::{
    collections::HashMap,
    env, fs,
    path::{Path, PathBuf},
    process::Command,
    sync::{Arc, Mutex},
    thread,
    time::Duration,
};

use base64::{engine::general_purpose, Engine as _};
use chrono::{DateTime, Utc};
use cpal::{
    traits::{DeviceTrait, HostTrait, StreamTrait},
    SampleFormat, StreamConfig,
};
use regex::Regex;
use reqwest::{
    blocking::Client,
    header::{CONTENT_TYPE, USER_AGENT},
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use tauri::{Manager, State};
use uuid::Uuid;

const GEMINI_MODEL: &str = "gemini-2.5-flash";
const GEMINI_TEMPERATURE: f32 = 0.8;
const GEMINI_TOP_P: f32 = 0.9;
const TTS_MODEL: &str = "eleven_v3";
const DEFAULT_ELEVENLABS_VOICE_ID: &str = "cgSgspJ2msm6clMCkdW9";

const SYSTEM_INSTRUCTION: &str = concat!(
    "Do NOT use emojis.",
    "You are Rose, a warm Thai girl friend, speaking Thai naturally like real conversation, not like an AI.",
    "Talk casual and friendly, like LINE chat or voice call. Use simple everyday Thai words and particles.",
    "Do NOT sound like a teacher or news reporter. Do NOT explain in a formal way. Do NOT say things like ",
    "'ในฐานะปัญญาประดิษฐ์', 'ฉันเป็น AI', 'โมเดลภาษา', or anything similar.",
    "Keep answers short and direct, usually 1-4 short sentences.",
    "Always respond to what the user just said; briefly acknowledge their feelings or repeat key words.",
    "Answer ONLY what the user asks, do NOT add long extra explanation unless they clearly ask for it.",
    "Do NOT make bullet lists or numbered lists. Do NOT structure like a report or essay.",
    "You are like a caring friend: you can ask back sometimes and give gentle suggestions, but keep it brief.",
    "You can work as an agent: open YouTube, open websites, open apps.",
    "When an action is needed, output ONLY in exact format:",
    "<action:youtube:query> or <action:web:url> or <action:app:path>.",
    "For YouTube searches, put the raw search words after youtube, including spaces if needed.",
    "Do NOT include any additional text inside the action tag.",
    "Do NOT wrap action tags in markdown or code blocks."
);

#[derive(Clone, Serialize)]
struct Message {
    role: String,
    content: String,
    created_at: String,
}

#[derive(Clone)]
struct Room {
    id: String,
    name: String,
    messages: Vec<Message>,
    created_at: String,
    updated_at: String,
}

#[derive(Serialize)]
struct RoomSummary {
    id: String,
    name: String,
    message_count: usize,
    last_message_preview: String,
    created_at: String,
    updated_at: String,
}

#[derive(Serialize)]
struct SpeechResponse {
    mime_type: String,
    base64: String,
}

#[derive(Debug)]
struct ActionCommand {
    kind: String,
    value: String,
}

#[derive(Clone)]
struct AppState {
    rooms: Arc<Mutex<HashMap<String, Room>>>,
    client: Client,
    action_pattern: Regex,
}

fn now_iso() -> String {
    let now: DateTime<Utc> = Utc::now();
    now.to_rfc3339()
}

impl Room {
    fn summary(&self) -> RoomSummary {
        RoomSummary {
            id: self.id.clone(),
            name: self.name.clone(),
            message_count: self.messages.len(),
            last_message_preview: self
                .messages
                .last()
                .map(|message| message.content.clone())
                .unwrap_or_else(|| "No messages yet".to_string()),
            created_at: self.created_at.clone(),
            updated_at: self.updated_at.clone(),
        }
    }
}

fn create_room_entry(name: Option<String>) -> Room {
    let timestamp = now_iso();
    Room {
        id: Uuid::new_v4().simple().to_string(),
        name: name
            .unwrap_or_else(|| "New Chat".to_string())
            .trim()
            .to_string()
            .if_empty("New Chat"),
        messages: Vec::new(),
        created_at: timestamp.clone(),
        updated_at: timestamp,
    }
}

trait EmptyDefault {
    fn if_empty(self, fallback: &str) -> String;
}

impl EmptyDefault for String {
    fn if_empty(self, fallback: &str) -> String {
        if self.is_empty() {
            fallback.to_string()
        } else {
            self
        }
    }
}

#[tauri::command]
fn get_rooms(state: State<AppState>) -> Result<Vec<RoomSummary>, String> {
    let mut rooms: Vec<Room> = state
        .rooms
        .lock()
        .map_err(|_| "Room state is unavailable".to_string())?
        .values()
        .cloned()
        .collect();

    rooms.sort_by(|left, right| right.updated_at.cmp(&left.updated_at));
    Ok(rooms.iter().map(Room::summary).collect())
}

#[tauri::command]
fn create_room(state: State<AppState>, name: Option<String>) -> Result<RoomSummary, String> {
    let room = create_room_entry(name);
    let summary = room.summary();
    state
        .rooms
        .lock()
        .map_err(|_| "Room state is unavailable".to_string())?
        .insert(room.id.clone(), room);
    Ok(summary)
}

#[tauri::command]
fn delete_room(state: State<AppState>, room_id: String) -> Result<bool, String> {
    let mut rooms = state
        .rooms
        .lock()
        .map_err(|_| "Room state is unavailable".to_string())?;

    if rooms.remove(&room_id).is_none() {
        return Err("Room not found".to_string());
    }

    if rooms.is_empty() {
        let room = create_room_entry(Some("New Chat".to_string()));
        rooms.insert(room.id.clone(), room);
    }

    Ok(true)
}

#[tauri::command]
fn rename_room(
    state: State<AppState>,
    room_id: String,
    new_name: String,
) -> Result<RoomSummary, String> {
    let mut rooms = state
        .rooms
        .lock()
        .map_err(|_| "Room state is unavailable".to_string())?;
    let room = rooms
        .get_mut(&room_id)
        .ok_or_else(|| "Room not found".to_string())?;

    room.name = new_name.trim().to_string().if_empty("Untitled Chat");
    room.updated_at = now_iso();
    Ok(room.summary())
}

#[tauri::command]
fn get_messages(state: State<AppState>, room_id: String) -> Result<Vec<Message>, String> {
    let rooms = state
        .rooms
        .lock()
        .map_err(|_| "Room state is unavailable".to_string())?;
    let room = rooms
        .get(&room_id)
        .ok_or_else(|| "Room not found".to_string())?;
    Ok(room.messages.clone())
}

#[tauri::command]
fn clear_room(state: State<AppState>, room_id: String) -> Result<bool, String> {
    let mut rooms = state
        .rooms
        .lock()
        .map_err(|_| "Room state is unavailable".to_string())?;
    let room = rooms
        .get_mut(&room_id)
        .ok_or_else(|| "Room not found".to_string())?;
    room.messages.clear();
    room.updated_at = now_iso();
    Ok(true)
}

#[tauri::command]
async fn send_message(
    state: State<'_, AppState>,
    room_id: String,
    user_message: String,
) -> Result<String, String> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        send_message_blocking(&state, room_id, user_message)
    })
    .await
    .map_err(|error| format!("Message task failed: {error}"))?
}

fn send_message_blocking(
    state: &AppState,
    room_id: String,
    user_message: String,
) -> Result<String, String> {
    let text = user_message.trim();
    if text.is_empty() {
        return Err("Message cannot be empty".to_string());
    }

    add_message(state, &room_id, "user", text)?;

    let reply = match generate_reply(state, &room_id) {
        Ok(reply) => reply,
        Err(error) => {
            let error_text = format!("Sorry, I could not get a response: {error}");
            let _ = add_message(state, &room_id, "assistant", &error_text);
            return Ok(error_text);
        }
    };

    if let Some(action) = parse_action(state, &reply)? {
        let spoken_reply = do_action(action);
        add_message(state, &room_id, "assistant", &reply)?;
        return Ok(spoken_reply);
    }

    add_message(state, &room_id, "assistant", &reply)?;
    Ok(reply)
}

#[tauri::command]
async fn synthesize_speech(
    state: State<'_, AppState>,
    text: String,
) -> Result<SpeechResponse, String> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || synthesize_speech_blocking(&state, text))
        .await
        .map_err(|error| format!("Speech synthesis task failed: {error}"))?
}

fn synthesize_speech_blocking(state: &AppState, text: String) -> Result<SpeechResponse, String> {
    let speech = text.trim();
    if speech.is_empty() {
        return Err("Speech text cannot be empty".to_string());
    }

    let api_key =
        env::var("ELEVENLABS_API_KEY").map_err(|_| "ELEVENLABS_API_KEY is not set".to_string())?;
    let voice_id =
        env::var("ELEVENLABS_VOICE_ID").unwrap_or_else(|_| DEFAULT_ELEVENLABS_VOICE_ID.to_string());
    let url = format!("https://api.elevenlabs.io/v1/text-to-speech/{voice_id}");

    let response = state
        .client
        .post(url)
        .header("xi-api-key", api_key)
        .json(&json!({
            "text": speech,
            "model_id": TTS_MODEL,
        }))
        .send()
        .map_err(|error| format!("ElevenLabs request failed: {error}"))?;

    if !response.status().is_success() {
        return Err(format!("ElevenLabs returned {}", response.status()));
    }

    let audio = response
        .bytes()
        .map_err(|error| format!("Could not read ElevenLabs audio: {error}"))?;

    Ok(SpeechResponse {
        mime_type: "audio/mpeg".to_string(),
        base64: general_purpose::STANDARD.encode(audio),
    })
}

#[tauri::command]
async fn listen_once(state: State<'_, AppState>) -> Result<String, String> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || listen_once_blocking(&state))
        .await
        .map_err(|error| format!("Listen task failed: {error}"))?
}

fn listen_once_blocking(state: &AppState) -> Result<String, String> {
    let wav_path = temp_audio_path("wav");
    let flac_path = temp_audio_path("flac");

    let result = (|| {
        let sample_rate = record_microphone_wav(&wav_path, Duration::from_secs(6))?;
        convert_wav_to_flac(&wav_path, &flac_path)?;
        recognize_google_speech(&state.client, &flac_path, sample_rate)
    })();

    let _ = fs::remove_file(&wav_path);
    let _ = fs::remove_file(&flac_path);

    result
}

fn add_message(
    state: &AppState,
    room_id: &str,
    role: &str,
    content: &str,
) -> Result<Message, String> {
    let mut rooms = state
        .rooms
        .lock()
        .map_err(|_| "Room state is unavailable".to_string())?;
    let room = rooms
        .get_mut(room_id)
        .ok_or_else(|| "Room not found".to_string())?;

    let message = Message {
        role: role.to_string(),
        content: content.to_string(),
        created_at: now_iso(),
    };
    room.messages.push(message.clone());
    room.updated_at = now_iso();
    Ok(message)
}

fn generate_reply(state: &AppState, room_id: &str) -> Result<String, String> {
    let messages = {
        let rooms = state
            .rooms
            .lock()
            .map_err(|_| "Room state is unavailable".to_string())?;
        rooms
            .get(room_id)
            .ok_or_else(|| "Room not found".to_string())?
            .messages
            .clone()
    };

    let contents: Vec<_> = messages
        .iter()
        .map(|message| {
            json!({
                "role": if message.role == "user" { "user" } else { "model" },
                "parts": [{ "text": message.content }],
            })
        })
        .collect();

    let api_key =
        env::var("GEMINI_API_KEY").map_err(|_| "GEMINI_API_KEY is not set".to_string())?;
    let url = format!(
        "https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    );

    let response = state
        .client
        .post(url)
        .json(&json!({
            "systemInstruction": {
                "parts": [{ "text": SYSTEM_INSTRUCTION }]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": GEMINI_TEMPERATURE,
                "topP": GEMINI_TOP_P
            }
        }))
        .send()
        .map_err(|error| format!("Gemini request failed: {error}"))?;

    if !response.status().is_success() {
        return Err(format!("Gemini returned {}", response.status()));
    }

    let body: GeminiResponse = response
        .json()
        .map_err(|error| format!("Could not parse Gemini response: {error}"))?;
    let text = body
        .candidates
        .into_iter()
        .next()
        .and_then(|candidate| candidate.content)
        .map(|content| {
            content
                .parts
                .into_iter()
                .filter_map(|part| part.text)
                .collect::<Vec<_>>()
                .join("")
        })
        .unwrap_or_default()
        .trim()
        .to_string();

    Ok(text)
}

fn parse_action(state: &AppState, reply: &str) -> Result<Option<ActionCommand>, String> {
    let Some(captures) = state.action_pattern.captures(reply) else {
        return Ok(None);
    };

    Ok(Some(ActionCommand {
        kind: captures
            .get(1)
            .map(|match_| match_.as_str().trim().to_lowercase())
            .unwrap_or_default(),
        value: captures
            .get(2)
            .map(|match_| match_.as_str().trim().to_string())
            .unwrap_or_default(),
    }))
}

fn do_action(action: ActionCommand) -> String {
    if action.value.is_empty() {
        return "โรสยังไม่เห็นสิ่งที่จะให้เปิดเลยนะ".to_string();
    }

    match action.kind.as_str() {
        "youtube" => {
            let query = url_encode(&action.value);
            let url = format!("https://www.youtube.com/results?search_query={query}");
            let _ = open::that(url);
            format!("โรสเปิด YouTube ค้นหา {} ให้แล้วนะ", action.value)
        }
        "web" => {
            let _ = open::that(action.value);
            "โรสเปิดเว็บให้แล้วนะ".to_string()
        }
        "app" => {
            #[cfg(target_os = "windows")]
            let _ = Command::new("cmd").args(["/C", &action.value]).spawn();

            #[cfg(not(target_os = "windows"))]
            let _ = Command::new("sh").args(["-c", &action.value]).spawn();

            "โรสเปิดแอปให้แล้วนะ".to_string()
        }
        _ => "โรสยังเปิดสิ่งนี้ให้ไม่ได้นะ".to_string(),
    }
}

fn url_encode(value: &str) -> String {
    value
        .bytes()
        .flat_map(|byte| match byte {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => {
                vec![byte as char]
            }
            b' ' => vec!['+'],
            _ => format!("%{byte:02X}").chars().collect(),
        })
        .collect()
}

fn temp_audio_path(extension: &str) -> PathBuf {
    env::temp_dir().join(format!(
        "rose_listen_{}.{}",
        Uuid::new_v4().simple(),
        extension
    ))
}

fn record_microphone_wav(path: &Path, duration: Duration) -> Result<u32, String> {
    let host = cpal::default_host();
    let device = host
        .default_input_device()
        .ok_or_else(|| "No default microphone found".to_string())?;
    let supported_config = device
        .default_input_config()
        .map_err(|error| format!("Could not read microphone config: {error}"))?;

    let sample_format = supported_config.sample_format();
    let config: StreamConfig = supported_config.into();
    let channels = usize::from(config.channels);
    let sample_rate = config.sample_rate.0;
    let samples = Arc::new(Mutex::new(Vec::<i16>::new()));
    let stream_samples = Arc::clone(&samples);
    let error_callback = |error| eprintln!("Microphone stream error: {error}");

    let stream = match sample_format {
        SampleFormat::F32 => device.build_input_stream(
            &config,
            move |data: &[f32], _| {
                push_f32_samples(data, channels, &stream_samples);
            },
            error_callback,
            None,
        ),
        SampleFormat::I16 => device.build_input_stream(
            &config,
            move |data: &[i16], _| {
                push_i16_samples(data, channels, &stream_samples);
            },
            error_callback,
            None,
        ),
        SampleFormat::U16 => device.build_input_stream(
            &config,
            move |data: &[u16], _| {
                push_u16_samples(data, channels, &stream_samples);
            },
            error_callback,
            None,
        ),
        other => return Err(format!("Unsupported microphone sample format: {other:?}")),
    }
    .map_err(|error| format!("Could not open microphone stream: {error}"))?;

    stream
        .play()
        .map_err(|error| format!("Could not start microphone stream: {error}"))?;
    thread::sleep(duration);
    drop(stream);

    let captured = samples
        .lock()
        .map_err(|_| "Could not read captured audio".to_string())?
        .clone();
    if captured.is_empty() {
        return Err("No microphone audio was captured".to_string());
    }

    let spec = hound::WavSpec {
        channels: 1,
        sample_rate,
        bits_per_sample: 16,
        sample_format: hound::SampleFormat::Int,
    };
    let mut writer = hound::WavWriter::create(path, spec)
        .map_err(|error| format!("WAV create failed: {error}"))?;
    for sample in captured {
        writer
            .write_sample(sample)
            .map_err(|error| format!("WAV write failed: {error}"))?;
    }
    writer
        .finalize()
        .map_err(|error| format!("WAV finalize failed: {error}"))?;

    Ok(sample_rate)
}

fn push_f32_samples(data: &[f32], channels: usize, samples: &Arc<Mutex<Vec<i16>>>) {
    if let Ok(mut captured) = samples.lock() {
        for frame in data.chunks(channels) {
            let sample = frame.first().copied().unwrap_or_default().clamp(-1.0, 1.0);
            captured.push((sample * f32::from(i16::MAX)) as i16);
        }
    }
}

fn push_i16_samples(data: &[i16], channels: usize, samples: &Arc<Mutex<Vec<i16>>>) {
    if let Ok(mut captured) = samples.lock() {
        for frame in data.chunks(channels) {
            captured.push(frame.first().copied().unwrap_or_default());
        }
    }
}

fn push_u16_samples(data: &[u16], channels: usize, samples: &Arc<Mutex<Vec<i16>>>) {
    if let Ok(mut captured) = samples.lock() {
        for frame in data.chunks(channels) {
            let sample = frame.first().copied().unwrap_or(32768);
            captured.push((i32::from(sample) - 32768) as i16);
        }
    }
}

fn convert_wav_to_flac(wav_path: &Path, flac_path: &Path) -> Result<(), String> {
    let output = Command::new("flac")
        .arg("--silent")
        .arg("--force")
        .arg("--best")
        .arg("-o")
        .arg(flac_path)
        .arg(wav_path)
        .output()
        .map_err(|error| {
            format!(
                "Could not run flac encoder: {error}. Install flac on Raspberry Pi with `sudo apt install flac`."
            )
        })?;

    if !output.status.success() {
        return Err(format!(
            "flac encoder failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }

    Ok(())
}

fn recognize_google_speech(
    client: &Client,
    flac_path: &Path,
    sample_rate: u32,
) -> Result<String, String> {
    let api_key = env::var("GOOGLE_SPEECH_API_KEY")
        .unwrap_or_else(|_| "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw".to_string());
    let audio =
        fs::read(flac_path).map_err(|error| format!("Could not read FLAC audio: {error}"))?;
    let url = format!(
        "https://www.google.com/speech-api/v2/recognize?client=chromium&lang=th-TH&key={api_key}"
    );

    let response = client
        .post(url)
        .header(USER_AGENT, "Mozilla/5.0")
        .header(CONTENT_TYPE, format!("audio/x-flac; rate={sample_rate}"))
        .body(audio)
        .send()
        .map_err(|error| format!("Speech recognition request failed: {error}"))?;

    if !response.status().is_success() {
        return Err(format!("Speech recognition returned {}", response.status()));
    }

    let body = response
        .text()
        .map_err(|error| format!("Could not read speech recognition response: {error}"))?;
    parse_google_speech_response(&body)
}

fn parse_google_speech_response(body: &str) -> Result<String, String> {
    for line in body.lines().filter(|line| !line.trim().is_empty()) {
        let Ok(value) = serde_json::from_str::<serde_json::Value>(line) else {
            continue;
        };
        let Some(transcript) = value
            .get("result")
            .and_then(|result| result.as_array())
            .and_then(|results| results.first())
            .and_then(|result| result.get("alternative"))
            .and_then(|alternatives| alternatives.as_array())
            .and_then(|alternatives| alternatives.first())
            .and_then(|alternative| alternative.get("transcript"))
            .and_then(|transcript| transcript.as_str())
        else {
            continue;
        };

        return Ok(transcript.trim().to_string());
    }

    Ok(String::new())
}

#[derive(Deserialize)]
struct GeminiResponse {
    candidates: Vec<GeminiCandidate>,
}

#[derive(Deserialize)]
struct GeminiCandidate {
    content: Option<GeminiContent>,
}

#[derive(Deserialize)]
struct GeminiContent {
    parts: Vec<GeminiPart>,
}

#[derive(Deserialize)]
struct GeminiPart {
    text: Option<String>,
}

pub fn run() {
    dotenvy::dotenv().ok();

    let mut rooms = HashMap::new();
    let room = create_room_entry(Some("New Chat".to_string()));
    rooms.insert(room.id.clone(), room);

    tauri::Builder::default()
        .manage(AppState {
            rooms: Arc::new(Mutex::new(rooms)),
            client: Client::new(),
            action_pattern: Regex::new(r"<\s*action\s*:\s*(youtube|web|app)\s*:\s*([^>]+?)\s*>")
                .expect("valid action regex"),
        })
        .setup(|app| {
            if let Some(window) = app.get_webview_window("main") {
                window.set_title("AI Chat")?;
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_rooms,
            create_room,
            delete_room,
            rename_room,
            get_messages,
            clear_room,
            listen_once,
            send_message,
            synthesize_speech
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
