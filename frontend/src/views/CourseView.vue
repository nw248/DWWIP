<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2>{{ course?.title }}</h2>
        <p class="text-muted">{{ course?.description }}</p>
      </div>
      <!-- Кнопка "Управление группами" ТОЛЬКО для преподавателя -->
      <button v-if="isTeacher" @click="addGroupToCourse" class="btn btn-secondary">Управление группами</button>
    </div>

    <div v-if="loading" class="text-center">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <!-- Для преподавателя: показываем группы -->
    <div v-else-if="isTeacher">
      <div v-if="groups.length === 0" class="alert alert-warning">
        Группы не добавлены на этот курс.
      </div>
      <div v-else class="row">
        <div v-for="group in groups" :key="group.id" class="col-md-3 mb-3">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">{{ group.name }}</h5>
              <p class="card-text">Студентов: {{ group.students_count || 0 }}</p>
              <p class="card-text">Уроков: {{ group.lessons_count || 0 }}</p>
              <button @click="goToGroup(group.id)" class="btn btn-primary">Управлять</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Для студента: показываем уроки -->
    <div v-else-if="isStudent">
      <div v-if="lessons.length === 0" class="alert alert-info">
        Уроков пока нет.
      </div>
      <div v-else class="list-group">
        <div v-for="lesson in lessons" :key="lesson.id" class="list-group-item">
          <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1">{{ lesson.title }}</h5>
            <small>{{ formatDate(lesson.created_at) }}</small>
          </div>
          <p class="mb-1">{{ lesson.content }}</p>
          <small>Тип: {{ lesson.lesson_type === 'test' ? 'Тест' : 'Текстовое задание' }}</small>
          <div class="mt-2">
            <button @click="goToLesson(lesson.id)" class="btn btn-primary btn-sm">Перейти</button>
          </div>
        </div>
      </div>
    </div>

    <button @click="goBack" class="btn btn-secondary mt-3">Назад</button>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../services/api'

export default {
  name: 'CourseView',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const courseId = route.params.id
    const course = ref(null)
    const groups = ref([])
    const lessons = ref([])
    const loading = ref(true)
    
    const userData = localStorage.getItem('user')
    const user = userData ? JSON.parse(userData) : null
    const isTeacher = user?.role === 'teacher'
    const isStudent = user?.role === 'student'

    const formatDate = (date) => {
      if (!date) return ''
      return new Date(date).toLocaleDateString('ru-RU')
    }

    const addGroupToCourse = () => {
      router.push(`/course/${courseId}/add-groups`)
    }

    const goToGroup = (groupId) => {
      router.push(`/course/${courseId}/group/${groupId}`)
    }

    const goToLesson = (lessonId) => {
      router.push(`/lesson/${lessonId}/group/${user?.group_id}`)
    }

    const goBack = () => {
      router.push('/')
    }

    const loadData = async () => {
      try {
        const courseRes = await api.get(`/courses/${courseId}`)
        course.value = courseRes.data
        
        if (isTeacher) {
          const groupsRes = await api.get(`/courses/${courseId}/groups`)
          groups.value = groupsRes.data
          console.log('Группы курса:', groups.value)
        } else if (isStudent && user?.group_id) {
          const lessonsRes = await api.get(`/courses/${courseId}/groups/${user.group_id}/lessons`)
          lessons.value = lessonsRes.data
          console.log('Уроки для студента:', lessons.value)
        }
      } catch (err) {
        console.error('Ошибка загрузки:', err)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadData()
    })

    return { 
      course, groups, lessons, loading, isTeacher, isStudent,
      formatDate, addGroupToCourse, goToGroup, goToLesson, goBack
    }
  }
}
</script>