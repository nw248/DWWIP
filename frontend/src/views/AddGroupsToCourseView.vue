<template>
  <div>
    <h2>Добавить группы к курсу</h2>
    <div class="card">
      <div class="card-body">
        <div v-if="loading" class="text-center">
          <div class="spinner-border text-primary" role="status"></div>
        </div>
        <div v-else-if="groups.length === 0" class="alert alert-warning">
          Нет доступных групп. Сначала создайте группы в админ-панели.
        </div>
        <div v-else>
          <div class="mb-3" v-for="group in groups" :key="group.id">
            <div class="form-check">
              <input class="form-check-input" type="checkbox" :value="group.id" v-model="selectedGroups" :id="'group'+group.id">
              <label class="form-check-label" :for="'group'+group.id">
                {{ group.name }} ({{ group.students_count || 0 }} студентов)
              </label>
            </div>
          </div>
          <button @click="saveGroups" class="btn btn-primary" :disabled="saving">Сохранить</button>
          <button @click="$router.back()" class="btn btn-secondary ms-2">Отмена</button>
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
  name: 'AddGroupsToCourseView',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const courseId = route.params.id
    const groups = ref([])
    const selectedGroups = ref([])
    const loading = ref(true)
    const saving = ref(false)

    onMounted(async () => {
      try {
        // Загружаем все группы
        const res = await api.get('/groups')
        groups.value = res.data
        console.log('Все группы:', groups.value)
        
        // Загружаем уже добавленные группы для этого курса
        const courseGroups = await api.get(`/courses/${courseId}/groups`)
        const existingGroupIds = courseGroups.data.map(g => g.id)
        selectedGroups.value = existingGroupIds
        console.log('Уже добавленные группы:', existingGroupIds)
      } catch (err) {
        console.error('Ошибка загрузки групп:', err)
        alert('Ошибка загрузки групп: ' + (err.response?.data?.error || err.message))
      } finally {
        loading.value = false
      }
    })

    const saveGroups = async () => {
      saving.value = true
      try {
        await api.post(`/courses/${courseId}/groups`, { groups: selectedGroups.value })
        router.push(`/course/${courseId}`)
      } catch (err) {
        console.error('Ошибка:', err)
        alert('Ошибка при добавлении групп: ' + (err.response?.data?.error || err.message))
      } finally {
        saving.value = false
      }
    }

    return { groups, selectedGroups, loading, saving, saveGroups }
  }
}
</script>