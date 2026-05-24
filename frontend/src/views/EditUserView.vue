<template>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card">
        <div class="card-header bg-warning text-dark">
          <h4 class="mb-0">Редактирование пользователя</h4>
        </div>
        <div class="card-body">
          <form @submit.prevent="submitForm">
            <div class="mb-3">
              <label class="form-label">Email</label>
              <input type="email" class="form-control" v-model="form.email" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Новый пароль</label>
              <div class="input-group">
                <input :type="showPassword ? 'text' : 'password'" class="form-control" v-model="form.new_password" @input="validatePassword" placeholder="Оставьте пустым, чтобы не менять">
                <button type="button" class="btn btn-outline-secondary" @click="togglePassword">
                  <i :class="showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
                </button>
              </div>
              <div class="mt-2" v-if="form.new_password">
                <div class="small" :class="passwordRules.length ? 'text-success' : 'text-danger'">
                  ✓ Минимум 8 символов
                </div>
                <div class="small" :class="passwordRules.hasUpperCase ? 'text-success' : 'text-danger'">
                  ✓ Хотя бы одна заглавная буква
                </div>
                <div class="small" :class="passwordRules.hasSymbol ? 'text-success' : 'text-danger'">
                  ✓ Хотя бы один специальный символ (!@#$%^&*)
                </div>
              </div>
              <small class="text-muted">Пароль должен содержать минимум 8 символов, одну заглавную букву и один спецсимвол</small>
            </div>
            <div class="mb-3">
              <label class="form-label">Полное имя</label>
              <input type="text" class="form-control" v-model="form.name" disabled>
              <small class="text-muted">Имя нельзя изменить</small>
            </div>
            <div class="mb-3">
              <label class="form-label">Роль</label>
              <input type="text" class="form-control" :value="getRoleName(form.role)" disabled>
              <small class="text-muted">Роль нельзя изменить</small>
            </div>
            <div class="mb-3" v-if="form.role === 'student'">
              <label class="form-label">Группа</label>
              <select class="form-control" v-model="form.group_id">
                <option :value="null">Без группы</option>
                <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
              </select>
              <small class="text-muted">Выберите группу для студента</small>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="loading || (form.new_password && !isPasswordValid)">Сохранить</button>
            <router-link to="/admin" class="btn btn-secondary ms-2">Отмена</router-link>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../services/api'

export default {
  name: 'EditUserView',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const userId = route.params.id
    const loading = ref(false)
    const groups = ref([])
    const showPassword = ref(false)
    const passwordRules = ref({
      length: false,
      hasUpperCase: false,
      hasSymbol: false
    })
    const form = ref({
      id: null,
      email: '',
      name: '',
      role: 'student',
      group_id: null,
      new_password: ''
    })

    const getRoleName = (role) => {
      const roles = { admin: 'Администратор', teacher: 'Преподаватель', student: 'Студент' }
      return roles[role] || role
    }

    const validatePassword = () => {
      const pwd = form.value.new_password
      passwordRules.value = {
        length: pwd.length >= 8,
        hasUpperCase: /[A-Z]/.test(pwd),
        hasSymbol: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd)
      }
    }

    const isPasswordValid = computed(() => {
      if (!form.value.new_password) return true
      return passwordRules.value.length && passwordRules.value.hasUpperCase && passwordRules.value.hasSymbol
    })

    const togglePassword = () => {
      showPassword.value = !showPassword.value
    }

    onMounted(async () => {
      try {
        const [userRes, groupsRes] = await Promise.all([
          api.get(`/users/${userId}`),
          api.get('/groups')
        ])
        form.value = {
          id: userRes.data.id,
          email: userRes.data.email,
          name: userRes.data.name,
          role: userRes.data.role,
          group_id: userRes.data.group_id,
          new_password: ''
        }
        groups.value = groupsRes.data
      } catch (err) {
        console.error('Ошибка загрузки:', err)
      }
    })

    const submitForm = async () => {
      if (form.value.new_password && !isPasswordValid.value) {
        alert('Пароль не соответствует требованиям безопасности')
        return
      }
      
      loading.value = true
      try {
        await api.put(`/users/${userId}`, {
          email: form.value.email,
          group_id: form.value.role === 'student' ? form.value.group_id : null,
          new_password: form.value.new_password
        })
        alert('Данные обновлены')
        router.push('/admin')
      } catch (err) {
        console.error('Ошибка:', err)
        alert('Ошибка при обновлении данных')
      } finally {
        loading.value = false
      }
    }

    return { 
      form, groups, loading, showPassword, passwordRules, isPasswordValid,
      getRoleName, validatePassword, togglePassword, submitForm 
    }
  }
}
</script>