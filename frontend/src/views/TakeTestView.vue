<template>
  <div>
    <h2>{{ lesson?.title }}</h2>
    <div class="card mb-4">
      <div class="card-body">
        <h5>Тест</h5>
        <p>{{ lesson?.content }}</p>
      </div>
    </div>

    <form @submit.prevent="submitTest">
      <div v-for="(question, idx) in questions" :key="question.id" class="card mb-3">
        <div class="card-body">
          <h5>Вопрос {{ idx + 1 }}: {{ question.text }}</h5>
          <div v-for="(option, optIdx) in question.options" :key="optIdx" class="form-check mt-2">
            <input 
              class="form-check-input" 
              type="radio" 
              :name="'q'+question.id" 
              :value="String.fromCharCode(65 + optIdx)"
              v-model="answers[question.id]"
            >
            <label class="form-check-label">
              {{ String.fromCharCode(65 + optIdx) }}) {{ option }}
            </label>
          </div>
        </div>
      </div>
      <button type="submit" class="btn btn-primary">Завершить тест</button>
      <button type="button" @click="$router.back()" class="btn btn-secondary ms-2">Отмена</button>
    </form>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../services/api'

export default {
  name: 'TakeTestView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const lessonId = route.params.lessonId
    const groupId = route.params.groupId
    const lesson = ref(null)
    const questions = ref([])
    const answers = ref({})

    onMounted(async () => {
      try {
        const [lessonRes, testRes] = await Promise.all([
          api.get(`/lessons/${lessonId}`),
          api.get(`/lessons/${lessonId}/test/start`)
        ])
        lesson.value = lessonRes.data
        questions.value = testRes.data
        console.log('Загружен тест:', questions.value)
      } catch (err) {
        console.error('Ошибка загрузки теста:', err)
        alert('Ошибка загрузки теста')
      }
    })

    const submitTest = async () => {
      try {
        const response = await api.post(`/lessons/${lessonId}/test/submit`, {
          answers: answers.value
        })
        alert(response.data.feedback)
        router.push(`/course/${lesson.value.course_id}/group/${groupId}`)
      } catch (err) {
        console.error('Ошибка отправки теста:', err)
        alert('Ошибка при отправке теста')
      }
    }

    return { lesson, questions, answers, submitTest }
  }
}
</script>