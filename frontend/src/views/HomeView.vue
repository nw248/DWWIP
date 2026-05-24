<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Мои курсы</h2>
      <button v-if="isTeacher" @click="createCourse" class="btn btn-success">+ Создать курс</button>
    </div>

    <div v-if="loading" class="text-center">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else-if="courses.length === 0" class="alert alert-info">
      <p v-if="isTeacher">У вас пока нет курсов. Нажмите "Создать курс".</p>
      <p v-else>Вы пока не добавлены ни на один курс. Обратитесь к преподавателю.</p>
    </div>

    <div v-else class="row">
      <div v-for="course in courses" :key="course.id" class="col-md-4 mb-3">
        <div class="card h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">{{ course.title }}</h5>
            <p class="card-text">{{ course.description || 'Описание отсутствует' }}</p>
            <p class="card-text">
              <small class="text-muted">Уроков: {{ course.lessons_count || 0 }}</small>
            </p>
            <button @click="goToCourse(course.id)" class="btn btn-primary btn-sm mt-2">Перейти к курсу</button>
            <div class="d-flex gap-2 mt-2">
              <button v-if="isTeacher || isAdmin" @click="editCourse(course.id)" class="btn btn-secondary btn-sm flex-fill">Редактировать</button>
              <button v-if="isTeacher || isAdmin" @click="deleteCourse(course.id)" class="btn btn-danger btn-sm flex-fill">Удалить</button>
            </div>
          </div>
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
  name: 'HomeView',
  setup() {
    const router = useRouter()
    const userData = localStorage.getItem('user')
    const user = userData ? JSON.parse(userData) : null
    const isTeacher = user?.role === 'teacher'
    const isAdmin = user?.role === 'admin'
    const courses = ref([])
    const loading = ref(true)

    const loadCourses = async () => {
      try {
        const response = await api.get('/courses')
        courses.value = response.data
        console.log('Загруженные курсы:', courses.value)
      } catch (err) {
        console.error('Ошибка загрузки курсов:', err)
      } finally {
        loading.value = false
      }
    }

    const createCourse = () => {
      router.push('/create-course')
    }

    const editCourse = (courseId) => {
      router.push(`/course/edit/${courseId}`)
    }

    const goToCourse = (courseId) => {
      router.push(`/course/${courseId}`)
    }

    const deleteCourse = async (courseId) => {
      if (!confirm('Удалить курс? Все уроки и задания будут удалены.')) return
      try {
        await api.delete(`/courses/${courseId}`)
        await loadCourses()
      } catch (err) {
        console.error('Ошибка удаления курса:', err)
        alert('Не удалось удалить курс')
      }
    }

    onMounted(() => {
      loadCourses()
    })

    return { courses, loading, isTeacher, isAdmin, createCourse, editCourse, goToCourse, deleteCourse }
  }
}
</script>