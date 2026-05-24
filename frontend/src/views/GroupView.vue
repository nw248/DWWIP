<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2>Группа: {{ groupName }}</h2>
        <h4>Курс: {{ courseTitle }}</h4>
      </div>
      <button @click="addLesson" class="btn btn-success">+ Добавить урок для группы</button>
    </div>

    <div v-if="loading" class="text-center">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else-if="lessons.length === 0" class="alert alert-info">
      Уроков пока нет. Добавьте первый урок.
    </div>

    <div v-else class="row">
      <div v-for="lesson in lessons" :key="lesson.id" class="col-md-6 mb-3">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">{{ lesson.title }}</h5>
            <p class="card-text">{{ lesson.content }}</p>
            <small class="text-muted">Тип: {{ lesson.lesson_type === 'test' ? 'Тест' : 'Текстовое задание' }}</small>
            
            <div class="mt-3">
              <div class="progress mb-2" style="height: 30px;">
                <div class="progress-bar" 
                     :class="lesson.progress === 100 ? 'bg-success' : (lesson.progress === 0 ? 'bg-danger' : 'bg-primary')"
                     :style="{ width: lesson.progress + '%' }">
                  {{ lesson.progress }}%
                </div>
              </div>
              <p class="text-muted">Выполнило: {{ lesson.completed }} / {{ lesson.total }}</p>
            </div>

            <button @click="checkLesson(lesson.id)" class="btn btn-primary mt-2">Проверить</button>
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
  name: 'GroupView',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const courseId = route.params.courseId
    const groupId = route.params.groupId
    const groupName = ref('')
    const courseTitle = ref('')
    const lessons = ref([])
    const loading = ref(true)

    const loadData = async () => {
      try {
        const [courseRes, groupRes, lessonsRes] = await Promise.all([
          api.get(`/courses/${courseId}`),
          api.get(`/groups/${groupId}`),
          api.get(`/courses/${courseId}/groups/${groupId}/lessons/progress`)
        ])
        courseTitle.value = courseRes.data.title
        groupName.value = groupRes.data.name
        lessons.value = lessonsRes.data
      } catch (err) {
        console.error('Ошибка загрузки:', err)
      } finally {
        loading.value = false
      }
    }

    const addLesson = () => {
      router.push(`/course/${courseId}/group/${groupId}/add-lesson`)
    }

    const checkLesson = (lessonId) => {
      router.push(`/grade/lesson/${lessonId}/group/${groupId}`)
    }

    const goBack = () => {
      router.push(`/course/${courseId}`)
    }

    onMounted(() => {
      loadData()
    })

    return { courseId, groupId, groupName, courseTitle, lessons, loading, addLesson, checkLesson, goBack }
  }
}
</script>