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
      <div v-for="question in questions" :key="question.id" class="card mb-3">
        <div class="card-body">
          <h5>Вопрос {{ index + 1 }}: {{ question.text }}</h5>
          <div class="form-check mt-2">
            <input class="form-check-input" type="radio" :name="'q'+question.id" value="A" v-model="answers[question.id]">
            <label class="form-check-label">A) {{ question.option_a }}</label>
          </div>
          <div class="form-check">
            <input class="form-check-input" type="radio" :name="'q'+question.id" value="B" v-model="answers[question.id]">
            <label class="form-check-label">B) {{ question.option_b }}</label>
          </div>
          <div class="form-check">
            <input class="form-check-input" type="radio" :name="'q'+question.id" value="C" v-model="answers[question.id]">
            <label class="form-check-label">C) {{ question.option_c }}</label>
          </div>
          <div class="form-check">
            <input class="form-check-input" type="radio" :name="'q'+question.id" value="D" v-model="answers[question.id]">
            <label class="form-check-label">D) {{ question.option_d }}</label>
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
    const index = 0

    onMounted(async () => {
      try {
        const [lessonRes, testRes] = await Promise.all([
          api.get(`/lessons/${lessonId}`),
          api.get(`/lessons/${lessonId}/test/start`)
        ])
        lesson.value = lessonRes.data
        questions.value = testRes.data
      } catch (err) {
        console.error('Ошибка загрузки теста:', err)
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

    return { lesson, questions, answers, submitTest, index }
  }
}
</script>