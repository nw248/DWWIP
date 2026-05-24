<template>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card">
        <div class="card-header bg-primary text-white">
          <h4 class="mb-0">Добавить пользователя</h4>
        </div>
        <div class="card-body">
          <form @submit.prevent="submitForm">
            <div class="mb-3">
              <label class="form-label">Email</label>
              <input type="email" class="form-control" v-model="form.email" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Пароль</label>
              <div class="input-group">
                <input :type="showPassword ? 'text' : 'password'" class="form-control" v-model="form.password" @input="validatePassword" required>
                <button type="button" class="btn btn-outline-secondary" @click="togglePassword">
                  <i :class="showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
                </button>
              </div>
              <div class="mt-2">
                <div class="small" :class="passwordRules.length >= 8 ? 'text-success' : 'text-danger'">
                  ✓ Минимум 8 символов
                </div>
                <div class="small" :class="passwordRules.hasUpperCase ? 'text-success' : 'text-danger'">
                  ✓ Хотя бы одна заглавная буква
                </div>
                <div class="small" :class="passwordRules.hasSymbol ? 'text-success' : 'text-danger'">
                  ✓ Хотя бы один специальный символ (!@#$%^&*)
                </div>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">Полное имя</label>
              <input type="text" class="form-control" v-model="form.name" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Роль</label>
              <select class="form-control" v-model="form.role">
                <option value="student">Студент</option>
                <option value="teacher">Преподаватель</option>
                <option value="admin">Администратор</option>
              </select>
            </div>
            <div class="mb-3" v-if="form.role === 'student'">
              <label class="form-label">Группа</label>
              <select class="form-control" v-model="form.group_id">
                <option :value="null">Без группы</option>
                <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
              </select>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="loading || !isPasswordValid">Добавить</button>
            <router-link to="/admin" class="btn btn-secondary ms-2">Отмена</router-link>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

export default {
  name: 'AddUserView',
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const groups = ref([])
    const showPassword = ref(false)
    const form = ref({
      email: '',
      password: '',
      name: '',
      role: 'student',
      group_id: null
    })
    const passwordRules = ref({
      length: false,
      hasUpperCase: false,
      hasSymbol: false
    })

    const validatePassword = () => {
      const pwd = form.value.password
      passwordRules.value = {
        length: pwd.length >= 8,
        hasUpperCase: /[A-Z]/.test(pwd),
        hasSymbol: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd)
      }
    }

    const isPasswordValid = computed(() => {
      return passwordRules.value.length && passwordRules.value.hasUpperCase && passwordRules.value.hasSymbol
    })

    const togglePassword = () => {
      showPassword.value = !showPassword.value
    }

    onMounted(async () => {
      try {
        const res = await api.get('/groups')
        groups.value = res.data
      } catch (err) {
        console.error('Ошибка загрузки групп:', err)
      }
    })

    const submitForm = async () => {
      if (!isPasswordValid.value) {
        alert('Пароль не соответствует требованиям безопасности')
        return
      }
      
      loading.value = true
      try {
        await api.post('/users', form.value)
        router.push('/admin')
      } catch (err) {
        console.error('Ошибка:', err)
        alert('Ошибка при добавлении пользователя')
      } finally {
        loading.value = false
      }
    }

    return { 
      form, groups, loading, showPassword, passwordRules, isPasswordValid, 
      validatePassword, togglePassword, submitForm 
    }
  }
}
</script>