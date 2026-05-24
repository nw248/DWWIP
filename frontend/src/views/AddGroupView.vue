<template>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card">
        <div class="card-header bg-primary text-white">
          <h4 class="mb-0">Добавить группу</h4>
        </div>
        <div class="card-body">
          <form @submit.prevent="submitForm">
            <div class="mb-3">
              <label class="form-label">Название группы</label>
              <input type="text" class="form-control" v-model="form.name" required>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="loading">Создать</button>
            <router-link to="/admin" class="btn btn-secondary ms-2">Отмена</router-link>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

export default {
  name: 'AddGroupView',
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const form = ref({ name: '' })

    const submitForm = async () => {
      loading.value = true
      try {
        await api.post('/groups', form.value)
        router.push('/admin')
      } catch (err) {
        console.error('Ошибка:', err)
        alert('Ошибка при добавлении группы')
      } finally {
        loading.value = false
      }
    }

    return { form, loading, submitForm }
  }
}
</script>