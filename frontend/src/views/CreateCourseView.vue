<template>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card">
        <div class="card-header bg-primary text-white">
          <h4 class="mb-0">Создать курс</h4>
        </div>
        <div class="card-body">
          <form @submit.prevent="handleSubmit">
            <div class="mb-3">
              <label class="form-label">Название курса *</label>
              <input type="text" class="form-control" v-model="title" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Описание курса</label>
              <textarea class="form-control" rows="4" v-model="description"></textarea>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="loading">
              {{ loading ? 'Создание...' : 'Создать' }}
            </button>
            <button type="button" @click="$router.back()" class="btn btn-secondary ms-2">Отмена</button>
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
  name: 'CreateCourseView',
  setup() {
    const router = useRouter()
    const title = ref('')
    const description = ref('')
    const loading = ref(false)

    const handleSubmit = async () => {
      if (!title.value.trim()) {
        alert('Название курса обязательно')
        return
      }
      loading.value = true
      try {
        await api.post('/courses', { title: title.value, description: description.value })
        router.push('/')
      } catch (err) {
        console.error('Ошибка:', err)
        alert('Ошибка при создании курса')
      } finally {
        loading.value = false
      }
    }

    return { title, description, loading, handleSubmit }
  }
}
</script>