import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('admin_token') || '',
    admin: JSON.parse(localStorage.getItem('admin_info') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state) => state.admin?.role || '',
  },
  actions: {
    setLogin(token, admin) {
      this.token = token
      this.admin = admin
      localStorage.setItem('admin_token', token)
      localStorage.setItem('admin_info', JSON.stringify(admin))
    },
    logout() {
      this.token = ''
      this.admin = null
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_info')
    },
  },
})
