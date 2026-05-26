<template>
  <div>
    <h2>Добавить урок для группы</h2>
    <div class="card">
      <div class="card-body">
        <form @submit.prevent="handleSubmit" enctype="multipart/form-data">
          <div class="mb-3">
            <label class="form-label">Название урока</label>
            <input type="text" class="form-control" v-model="title" required>
          </div>
          <div class="mb-3">
            <label class="form-label">Содержание урока</label>
            <textarea class="form-control" rows="5" v-model="content" required></textarea>
          </div>
          <div class="mb-3">
            <label class="form-label">Тип урока</label>
            <select class="form-control" v-model="lessonType">
              <option value="lecture">Лекция (только чтение)</option>
              <option value="text">Текстовое задание</option>
              <option value="test">Тест</option>
            </select>
          </div>
          
          <div class="mb-3">
            <label class="form-label">Прикреплённые файлы</label>
            <input type="file" class="form-control" @change="handleFileUpload" multiple>
            <small class="text-muted">Можно выбрать несколько файлов (PDF, DOC, DOCX, TXT, ZIP, изображения)</small>
            <div v-if="files.length > 0" class="mt-2">
              <div v-for="(file, index) in files" :key="index" class="d-flex justify-content-between align-items-center mb-1">
                <span>{{ file.name }}</span>
                <button type="button" class="btn btn-sm btn-danger" @click="removeFile(index)">Удалить</button>
              </div>
            </div>
          </div>
          
          <div v-if="lessonType === 'test'" class="mb-3">
            <h5>Вопросы теста</h5>
            <div v-for="(q, qIndex) in questions" :key="qIndex" class="card mb-3 p-3">
              <div class="mb-2">
                <label class="form-label">Текст вопроса {{ qIndex + 1 }}</label>
                <input type="text" class="form-control" v-model="q.text" required>
              </div>
              
              <div class="mb-2">
                <label class="form-label">Варианты ответов</label>
                <div v-for="(opt, optIndex) in q.options" :key="optIndex" class="input-group mb-2">
                  <span class="input-group-text">{{ String.fromCharCode(65 + optIndex) }}</span>
                  <input type="text" class="form-control" v-model="opt.text" placeholder="Вариант ответа" required>
                  <button type="button" class="btn btn-danger" @click="removeOption(qIndex, optIndex)" v-if="q.options.length > 1">×</button>
                </div>
                <button type="button" class="btn btn-sm btn-secondary" @click="addOption(qIndex)">+ Добавить вариант ответа</button>
              </div>
              
              <div class="mb-2">
                <label class="form-label">Правильные ответы</label>
                <div class="form-check" v-for="(opt, optIndex) in q.options" :key="optIndex">
                  <input class="form-check-input" type="checkbox" :value="String.fromCharCode(65 + optIndex)" v-model="q.correct_answers">
                  <label class="form-check-label">
                    {{ String.fromCharCode(65 + optIndex) }}: {{ opt.text || '(пусто)' }}
                  </label>
                </div>
                <small class="text-muted">Можно выбрать несколько правильных ответов</small>
              </div>
              
              <button type="button" class="btn btn-danger btn-sm mt-2" @click="removeQuestion(qIndex)">Удалить вопрос</button>
            </div>
            <button type="button" @click="addQuestion" class="btn btn-secondary">+ Добавить вопрос</button>
          </div>
          
          <button type="submit" class="btn btn-primary mt-3">Создать урок</button>
          <button type="button" @click="$router.back()" class="btn btn-secondary mt-3 ms-2">Отмена</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../services/api'

export default {
  name: 'AddLessonView',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const courseId = route.params.courseId
    const groupId = route.params.groupId
    
    const title = ref('')
    const content = ref('')
    const lessonType = ref('lecture')
    const questions = ref([])
    const files = ref([])

    const handleFileUpload = (event) => {
      const newFiles = Array.from(event.target.files)
      files.value.push(...newFiles)
    }

    const removeFile = (index) => {
      files.value.splice(index, 1)
    }

    const addOption = (qIndex) => {
      questions.value[qIndex].options.push({ text: '' })
    }

    const removeOption = (qIndex, optIndex) => {
      questions.value[qIndex].options.splice(optIndex, 1)
      const maxIndex = questions.value[qIndex].options.length
      questions.value[qIndex].correct_answers = questions.value[qIndex].correct_answers.filter(
        a => a.charCodeAt(0) - 65 < maxIndex
      )
    }

    const addQuestion = () => {
      questions.value.push({
        text: '',
        options: [{ text: '' }, { text: '' }],
        correct_answers: []
      })
    }

    const removeQuestion = (qIndex) => {
      questions.value.splice(qIndex, 1)
    }

    const handleSubmit = async () => {
      const formData = new FormData()
      formData.append('title', title.value)
      formData.append('content', content.value)
      formData.append('lesson_type', lessonType.value)
      
      files.value.forEach(file => {
        formData.append('files', file)
      })
      
      if (lessonType.value === 'test') {
        // ВАЖНО: questions отправляем как JSON-строку
        const questionsData = questions.value.map(q => ({
          text: q.text,
          options: q.options.map(opt => opt.text),
          correct_answers: q.correct_answers  // Это массив, например ['A', 'B']
        }))
        formData.append('questions', JSON.stringify(questionsData))
      }
      
      try {
        await api.post(`/courses/${courseId}/groups/${groupId}/lessons`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        router.push(`/course/${courseId}/group/${groupId}`)
      } catch (err) {
        console.error('Ошибка:', err)
        alert('Ошибка при создании урока: ' + (err.response?.data?.error || err.message))
      }
    }

    return { 
      title, content, lessonType, questions, files,
      handleFileUpload, removeFile,
      addOption, removeOption, addQuestion, removeQuestion, handleSubmit
    }
  }
}
</script>