<template>
  <div>
    <h2>{{ lesson?.title }}</h2>
    <div class="card mb-4">
      <div class="card-body">
        <h5>Задание</h5>
        <p>{{ lesson?.content }}</p>
        <small class="text-muted">Группа: {{ groupName }}</small>
        
        <!-- Отображение прикреплённых файлов урока -->
        <div v-if="lesson?.files && lesson.files.length > 0" class="mt-3">
          <h6>Материалы урока:</h6>
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
    
    <h4>Выполненные задания</h4>
    <div v-if="assignments.length === 0" class="alert alert-info">
      Нет выполненных заданий
    </div>
    
    <div v-for="assignment in assignments" :key="assignment.id" class="card mb-3">
      <div class="card-body">
        <h5>{{ assignment.student_name }}</h5>
        <p><strong>Дата сдачи:</strong> {{ formatDate(assignment.submitted_at) }}</p>
        
        <div v-if="lesson?.lesson_type === 'test'">
          <p><strong>Результат теста:</strong> {{ assignment.score }} / {{ assignment.total_questions || 0 }}</p>
          <p><strong>Комментарий:</strong> {{ assignment.feedback || 'Нет комментария' }}</p>
        </div>
        
        <div v-else>
          <p><strong>Ответ:</strong></p>
          <div class="alert alert-light">{{ assignment.answer_text || 'Нет текстового ответа' }}</div>
          <p v-if="assignment.answer_file">
            <a :href="`/uploads/${assignment.answer_file}`" target="_blank" class="btn btn-sm btn-info">Скачать файл</a>
          </p>
        </div>
        
        <div class="row mt-3">
          <div class="col-md-3">
            <label class="form-label">Оценка (0-100)</label>
            <input type="number" class="form-control" v-model.number="assignment.score" min="0" max="100">
          </div>
          <div class="col-md-7">
            <label class="form-label">Комментарий</label>
            <input type="text" class="form-control" v-model="assignment.feedback">
          </div>
          <div class="col-md-2">
            <button @click="saveGrade(assignment)" class="btn btn-primary mt-4">Сохранить</button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="mt-3 d-flex gap-2">
      <button @click="goBack" class="btn btn-secondary">Назад</button>
      <button @click="deleteLesson" class="btn btn-danger">Удалить урок</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../services/api'

export default {
  name: 'GradeView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const lessonId = route.params.lessonId
    const groupId = route.params.groupId
    const lesson = ref(null)
    const assignments = ref([])
    const groupName = ref('')

    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('ru-RU')
    }

    const goBack = () => {
      router.push(`/course/${lesson.value?.course_id}/group/${groupId}`)
    }

    const deleteLesson = async () => {
      if (!confirm('Удалить урок? Все ответы студентов будут удалены.')) return
      try {
        await api.delete(`/lessons/${lessonId}`)
        alert('Урок удалён')
        router.push(`/course/${lesson.value?.course_id}/group/${groupId}`)
      } catch (err) {
        console.error('Ошибка удаления:', err)
        alert('Ошибка при удалении урока')
      }
    }

    const saveGrade = async (assignment) => {
      try {
        await api.post(`/assignments/${assignment.id}/grade`, {
          score: assignment.score,
          feedback: assignment.feedback
        })
        alert('Оценка сохранена')
      } catch (err) {
        console.error('Ошибка сохранения:', err)
        alert('Ошибка при сохранении оценки')
      }
    }

    const loadData = async () => {
      try {
        const [lessonRes, assignRes, groupRes] = await Promise.all([
          api.get(`/lessons/${lessonId}`),
          api.get(`/lessons/${lessonId}/groups/${groupId}/assignments`),
          api.get(`/groups/${groupId}`)
        ])
        lesson.value = lessonRes.data
        assignments.value = assignRes.data
        groupName.value = groupRes.data.name
        
        // Для тестов добавляем количество вопросов
        if (lesson.value?.lesson_type === 'test') {
          const testRes = await api.get(`/lessons/${lessonId}/test/start`)
          const totalQuestions = testRes.data.length
          assignments.value.forEach(a => {
            a.total_questions = totalQuestions
          })
        }
        
        console.log('Загружен урок:', lesson.value)
        console.log('Файлы урока:', lesson.value?.files)
      } catch (err) {
        console.error('Ошибка загрузки:', err)
      }
    }

    onMounted(() => {
      loadData()
    })

    return { 
      lesson, assignments, groupName, formatDate, 
      goBack, deleteLesson, saveGrade 
    }
  }
}
</script>