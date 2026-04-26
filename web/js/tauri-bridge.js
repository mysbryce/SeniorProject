;(function () {
  function invoke(command, args = {}) {
    return window.__TAURI__.core.invoke(command, args)
  }

  window.pywebview = {
    api: {
      get_rooms: () => invoke('get_rooms'),
      create_room: (name = 'New Chat') => invoke('create_room', { name }),
      delete_room: (roomId) => invoke('delete_room', { roomId }),
      rename_room: (roomId, newName) => invoke('rename_room', { roomId, newName }),
      get_messages: (roomId) => invoke('get_messages', { roomId }),
      clear_room: (roomId) => invoke('clear_room', { roomId }),
      listen_once: () => invoke('listen_once'),
      send_message: (roomId, userMessage) => invoke('send_message', { roomId, userMessage }),
      synthesize_speech: (text) => invoke('synthesize_speech', { text }),
    },
  }

  window.addEventListener('DOMContentLoaded', () => {
    window.dispatchEvent(new Event('pywebviewready'))
  })
})()
