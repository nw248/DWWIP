<template>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card">
        <div class="card-header bg-warning text-dark">
          <h4 class="mb-0">Редактирование курса</h4>
        </div>
        <div class="card-body">
          <div v-if="loading" class="text-center">
            <div class="spinner-border text-primary" role="status"></div>
          </div>
          <form v-else @submit.prevent="submitForm">
            <div class="mb-3">
              <label class="form-label">Название курса</label>
              <input type="text" class="form-control" v-model="form.title" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Описание курса</label>
              <textarea class="form-control" rows="4" v-model="form.description"></textarea>
            </div>
            <div class="mb-3" v-if="isAdmin">
              <label class="form-label">Преподаватели</label>
              <select class="form-control" v-model="form.teacher_ids" multiple>
                <option v-for="teacher in teachers" :key="teacher.id" :value="teacher.id">
                  {{ teacher.name }} ({{ teacher.email }})
                </option>
              </select>
              <small class="text-muted">Удерживайте Ctrl для выбора нескольких</small>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="saving">Сохранить изменения</button>
            <button type="button" @click="goBack" class="btn btn-secondary ms-2">Отмена</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../services/api'

export default {
  name: 'EditCourseView',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const courseId = route.params.id
    const loading = ref(true)
    const saving = ref(false)
    const teachers = ref([])
    
    const userData = localStorage.getItem('user')
    const user = userData ? JSON.parse(userData) : null
    const isAdmin = user?.role === 'admin'
    
    const form = ref({
      title: '',
      description: '',
      teacher_ids: []
    })

    const goBack = () => {
      // Если администратор — возвращаемся в админ-панель
      if (isAdmin) {
        router.push('/admin')
      } else {
        router.push('/')
      }
    }

    onMounted(async () => {
      try {
        const courseRes = await api.get(`/courses/${courseId}`)
        form.value = {
          title: courseRes.data.title,
          description: courseRes.data.description || '',
          teacher_ids: []
        }
        
        if (isAdmin) {
          const usersRes = await api.get('/users')
          teachers.value = usersRes.data.filter(t => t.role === 'teacher')
        }
        
        console.log('Загружен курс:', courseRes.data)
      } catch (err) {
        console.error('Ошибка загрузки:', err)
        alert('Ошибка загрузки данных курса')
      } finally {
        loading.value = false
      }
    })

    const submitForm = async () => {
      saving.value = true
      try {
        await api.put(`/courses/${courseId}`, {
          title: form.value.title,
          description: form.value.description,
          teacher_ids: form.value.teacher_ids
        })
        alert('Курс успешно обновлён')
        goBack()
      } catch (err) {
        console.error('Ошибка:', err)
        alert('Ошибка при обновлении курса')
      } finally {
        saving.value = false
      }
    }

    return { form, teachers, loading, saving, isAdmin, goBack, submitForm }
  }
}
</script>