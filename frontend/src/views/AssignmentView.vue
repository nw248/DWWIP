<template>
  <div>
    <h2>{{ lesson?.title }}</h2>
    <div class="card mb-4">
      <div class="card-body">
        <h5>Содержание</h5>
        <p>{{ lesson?.content }}</p>
        <small class="text-muted">Тип: {{ getLessonTypeName(lesson?.lesson_type) }}</small>
        
        <!-- Отображение прикреплённых файлов урока -->
        <div v-if="lesson?.files && lesson.files.length > 0" class="mt-3">
          <h6>Материалы для скачивания:</h6>
          <ul>
            <li v-for="file in lesson.files" :key="file">
              <a :href="`/uploads/${file}`" target="_blank" class="btn btn-sm btn-outline-primary mt-1">
                📎 {{ file }}
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Лекция: только чтение, без формы отправки -->
    <div v-if="lesson?.lesson_type === 'lecture'" class="alert alert-info">
      <i class="bi bi-info-circle"></i> Это лекция. Задание не требуется.
    </div>

    <!-- Отображение отправленного ответа и оценки -->
    <div v-else-if="existingAssignment" class="alert alert-info mb-4">
      <h5>Ваш ответ</h5>
      <p>{{ existingAssignment.answer_text || 'Текстовый ответ не был введён' }}</p>
      <p v-if="existingAssignment.answer_file">
        <a :href="`/uploads/${existingAssignment.answer_file}`" target="_blank" class="btn btn-sm btn-info">Скачать файл</a>
      </p>
      <p><strong>Дата сдачи:</strong> {{ formatDate(existingAssignment.submitted_at) }}</p>
      <hr>
      <p v-if="existingAssignment.score !== null"><strong>Оценка:</strong> {{ existingAssignment.score }}</p>
      <p v-if="existingAssignment.feedback"><strong>Комментарий преподавателя:</strong> {{ existingAssignment.feedback }}</p>
      
      <button v-if="!isEditing" @click="startEditing" class="btn btn-warning mt-2">Редактировать ответ</button>
    </div>

    <!-- Форма отправки ответа (только для текстовых заданий) -->
    <div v-else-if="lesson?.lesson_type === 'text'" class="card">
      <div class="card-body">
        <h5>Ваш ответ</h5>
        <form @submit.prevent="submitAnswer" enctype="multipart/form-data">
          <div class="mb-3">
            <label class="form-label">Текстовый ответ</label>
            <textarea class="form-control" rows="8" v-model="answerText" placeholder="Введите ответ..."></textarea>
          </div>
          <div class="mb-3">
            <label class="form-label">Или загрузить файл</label>
            <input type="file" class="form-control" @change="handleFileUpload">
          </div>
          <button type="submit" class="btn btn-primary" :disabled="loading">Отправить</button>
        </form>
      </div>
    </div>

    <!-- Форма редактирования ответа -->
    <div v-if="isEditing" class="card mt-3">
      <div class="card-body">
        <h5>Редактировать ответ</h5>
        <form @submit.prevent="updateAnswer" enctype="multipart/form-data">
          <div class="mb-3">
            <label class="form-label">Текстовый ответ</label>
            <textarea class="form-control" rows="8" v-model="editAnswerText" placeholder="Введите ответ..."></textarea>
          </div>
          <div class="mb-3">
            <label class="form-label">Или загрузить файл</label>
            <input type="file" class="form-control" @change="handleFileUploadEdit">
            <small class="text-muted" v-if="existingAssignment?.answer_file">Текущий файл: {{ existingAssignment.answer_file }}</small>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="loading">Сохранить изменения</button>
          <button type="button" @click="cancelEditing" class="btn btn-secondary ms-2">Отмена</button>
        </form>
      </div>
    </div>

    <div v-if="loading" class="text-center mt-3">
      <div class="spinner-border text-primary" role="status"></div>
    </div>
    <div v-if="submitted" class="alert alert-success mt-3">Задание успешно обновлено!</div>
    <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../services/api'

export default {
  name: 'AssignmentView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const lessonId = route.params.lessonId
    const groupId = route.params.groupId
    const lesson = ref(null)
    const existingAssignment = ref(null)
    const answerText = ref('')
    const editAnswerText = ref('')
    const selectedFile = ref(null)
    const selectedEditFile = ref(null)
    const loading = ref(false)
    const submitted = ref(false)
    const error = ref('')
    const isEditing = ref(false)

    const userData = localStorage.getItem('user')
    const user = userData ? JSON.parse(userData) : null

    const getLessonTypeName = (type) => {
      const types = { lecture: 'Лекция', text: 'Текстовое задание', test: 'Тест' }
      return types[type] || type
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('ru-RU')
    }

    const loadData = async () => {
      try {
        const [lessonRes, assignmentRes] = await Promise.all([
          api.get(`/lessons/${lessonId}`),
          api.get(`/assignments/lesson/${lessonId}`).catch(() => ({ data: null }))
        ])
        lesson.value = lessonRes.data
        existingAssignment.value = assignmentRes.data
        
        console.log('Загружен урок:', lesson.value)
        console.log('Файлы урока:', lesson.value?.files)
        
        if (lesson.value.lesson_type === 'test' && !existingAssignment.value) {
          router.replace(`/test/lesson/${lessonId}/group/${groupId}`)
        }
      } catch (err) {
        console.error('Ошибка загрузки:', err)
        error.value = 'Ошибка загрузки урока'
      }
    }

    const startEditing = () => {
      editAnswerText.value = existingAssignment.value?.answer_text || ''
      isEditing.value = true
    }

    const cancelEditing = () => {
      isEditing.value = false
      editAnswerText.value = ''
      selectedEditFile.value = null
    }

    const handleFileUpload = (event) => {
      selectedFile.value = event.target.files[0]
    }

    const handleFileUploadEdit = (event) => {
      selectedEditFile.value = event.target.files[0]
    }

    const updateAnswer = async () => {
      loading.value = true
      error.value = ''
      
      const formData = new FormData()
      formData.append('answer_text', editAnswerText.value)
      if (selectedEditFile.value) {
        formData.append('answer_file', selectedEditFile.value)
      }
      
      try {
        await api.post(`/lessons/${lessonId}/update`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        submitted.value = true
        isEditing.value = false
        setTimeout(() => {
          loadData()
          submitted.value = false
        }, 1500)
      } catch (err) {
        console.error('Ошибка обновления:', err)
        error.value = err.response?.data?.error || 'Ошибка при обновлении ответа'
      } finally {
        loading.value = false
      }
    }

    const submitAnswer = async () => {
      loading.value = true
      error.value = ''
      
      const formData = new FormData()
      formData.append('answer_text', answerText.value)
      if (selectedFile.value) {
        formData.append('answer_file', selectedFile.value)
      }
      
      try {
        await api.post(`/lessons/${lessonId}/submit`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        submitted.value = true
        setTimeout(() => {
          router.push(`/course/${lesson.value.course_id}`)
        }, 1500)
      } catch (err) {
        console.error('Ошибка отправки:', err)
        error.value = err.response?.data?.error || 'Ошибка при отправке ответа'
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadData()
    })

    return { 
      lesson, existingAssignment, answerText, editAnswerText, loading, submitted, error, isEditing,
      getLessonTypeName, formatDate, handleFileUpload, handleFileUploadEdit,
      startEditing, cancelEditing, updateAnswer, submitAnswer
    }
  }
}
</script>