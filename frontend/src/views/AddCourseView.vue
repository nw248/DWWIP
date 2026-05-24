<template>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card">
        <div class="card-header bg-primary text-white">
          <h4 class="mb-0">Добавить курс</h4>
        </div>
        <div class="card-body">
          <form @submit.prevent="submitForm">
            <div class="mb-3">
              <label class="form-label">Название курса</label>
              <input type="text" class="form-control" v-model="form.title" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Описание курса</label>
              <textarea class="form-control" rows="4" v-model="form.description"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Преподаватели</label>
              <select class="form-control" v-model="form.teacher_ids" multiple>
                <option v-for="teacher in teachers" :key="teacher.id" :value="teacher.id">
                  {{ teacher.name }} ({{ teacher.email }})
                </option>
              </select>
              <small class="text-muted">Удерживайте Ctrl для выбора нескольких</small>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="loading">Создать</button>
            <router-link to="/admin" class="btn btn-secondary ms-2">Отмена</router-link>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

export default {
  name: 'AddCourseView',
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const teachers = ref([])
    const form = ref({
      title: '',
      description: '',
      teacher_ids: []
    })

    onMounted(async () => {
      try {
        const usersRes = await api.get('/users')
        teachers.value = usersRes.data.filter(u => u.role === 'teacher')
      } catch (err) {
        console.error('Ошибка загрузки преподавателей:', err)
      }
    })

    const submitForm = async () => {
      loading.value = true
      try {
        await api.post('/courses', form.value)
        router.push('/admin')
      } catch (err) {
        console.error('Ошибка:', err)
        alert('Ошибка при добавлении курса')
      } finally {
        loading.value = false
      }
    }

    return { form, teachers, loading, submitForm }
  }
}
</script>