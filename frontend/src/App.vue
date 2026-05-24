<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid">
        <a class="navbar-brand" href="#" @click.prevent="goHome">СДО</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav ms-auto">
            <template v-if="user">
              <li class="nav-item">
                <span class="nav-link">{{ user.name }} ({{ getUserRoleName(user.role) }})</span>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="#" @click.prevent="logout">Выйти</a>
              </li>
            </template>
          </ul>
        </div>
      </div>
    </nav>

    <div class="container mt-4">
      <router-view @user-updated="loadUser" />
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from './services/api'

export default {
  name: 'App',
  setup() {
    const router = useRouter()
    const user = ref(null)

    const getUserRoleName = (role) => {
      const roles = { admin: 'Администратор', teacher: 'Преподаватель', student: 'Студент' }
      return roles[role] || role
    }

    const loadUser = () => {
      const userData = localStorage.getItem('user')
      if (userData) {
        user.value = JSON.parse(userData)
      } else {
        user.value = null
      }
    }

    const goHome = () => {
      if (!user.value) {
        router.push('/login')
        return
      }
      if (user.value.role === 'admin') {
        router.push('/admin')
      } else {
        router.push('/')
      }
    }

    const logout = async () => {
      try {
        await api.post('/logout')
      } catch (e) {
        console.error('Logout error:', e)
      }
      localStorage.removeItem('user')
      user.value = null
      router.push('/login')
    }

    // Загружаем пользователя при монтировании
    onMounted(() => {
      loadUser()
    })

    // Следим за изменением localStorage (если логин из другой вкладки)
    window.addEventListener('storage', () => {
      loadUser()
    })

    return { user, getUserRoleName, goHome, logout }
  }
}
</script>

<style>
@import 'bootstrap/dist/css/bootstrap.min.css';
@import 'bootstrap-icons/font/bootstrap-icons.css';

body {
  background-color: #f5f5f5;
}
.container {
  background-color: white;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  min-height: 500px;
}
.navbar {
  margin-bottom: 20px;
}
</style>