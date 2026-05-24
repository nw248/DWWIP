<template>
  <div class="row justify-content-center">
    <div class="col-md-5">
      <div class="card shadow">
        <div class="card-header bg-primary text-white text-center">
          <h4>Вход в систему</h4>
        </div>
        <div class="card-body">
          <form @submit.prevent="handleLogin">
            <div class="mb-3">
              <label class="form-label">Email</label>
              <input type="email" class="form-control" v-model="email" required autofocus>
            </div>
            <div class="mb-3">
              <label class="form-label">Пароль</label>
              <div class="input-group">
                <input :type="showPassword ? 'text' : 'password'" class="form-control" v-model="password" required>
                <button type="button" class="btn btn-outline-secondary" @click="showPassword = !showPassword">
                  <i :class="showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
                </button>
              </div>
            </div>
            <button type="submit" class="btn btn-primary w-100">Войти</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter()
    const email = ref('')
    const password = ref('')
    const showPassword = ref(false)

    const handleLogin = async () => {
      try {
        const response = await api.post('/login', {
          email: email.value,
          password: password.value
        })
        
        if (response.data.success) {
          const user = response.data.user
          localStorage.setItem('user', JSON.stringify(user))
          
          // Принудительно обновляем localStorage в других вкладках
          window.dispatchEvent(new Event('storage'))
          
          // Перенаправляем в зависимости от роли
          if (user.role === 'admin') {
            router.push('/admin')
          } else {
            router.push('/')
          }
        } else {
          alert(response.data.message)
        }
      } catch (err) {
        console.error('Ошибка входа:', err)
        alert('Ошибка при входе')
      }
    }

    return { email, password, showPassword, handleLogin }
  }
}
</script>