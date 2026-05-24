<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Панель администратора</h2>
      <button @click="createBackup" class="btn btn-success" :disabled="backupLoading">
        <span v-if="backupLoading" class="spinner-border spinner-border-sm me-1"></span>
        📀 Создать резервную копию
      </button>
    </div>

    <!-- Карточки статистики -->
    <div class="row g-4 mb-5">
      <div class="col-md-3">
        <div class="card text-center border-primary shadow-sm h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title text-primary">Пользователи</h5>
            <p class="display-4 flex-grow-1">{{ stats.users }}</p>
            <button @click="showUsers = true; showGroups = false; showCourses = false" class="btn btn-outline-primary btn-sm mt-auto">Управление</button>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card text-center border-primary shadow-sm h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title text-primary">Группы</h5>
            <p class="display-4 flex-grow-1">{{ stats.groups }}</p>
            <button @click="showGroups = true; showUsers = false; showCourses = false" class="btn btn-outline-primary btn-sm mt-auto">Управление</button>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card text-center border-primary shadow-sm h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title text-primary">Курсы</h5>
            <p class="display-4 flex-grow-1">{{ stats.courses }}</p>
            <button @click="showCourses = true; showUsers = false; showGroups = false" class="btn btn-outline-primary btn-sm mt-auto">Управление</button>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card text-center border-primary shadow-sm h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title text-primary">Преподаватели</h5>
            <p class="display-4 flex-grow-1">{{ stats.teachers }}</p>
            <div class="mt-auto" style="height: 31px;"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Список пользователей -->
    <!-- Список пользователей -->
    <div v-if="showUsers" class="mt-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h3>Список пользователей</h3>
        <router-link to="/admin/users/add" class="btn btn-primary">Добавить пользователя</router-link>
      </div>
      <div class="table-responsive">
        <table class="table table-striped table-bordered table-hover align-middle">
          <thead class="table-primary">
            <tr>
              <th style="width: 60px">ID</th>
              <th>Имя</th>
              <th>Email</th>
              <th style="width: 140px">Роль</th>
              <th style="width: 120px">Группа</th>
              <th style="width: 220px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td class="text-center">{{ user.id }}</td>
              <td>{{ user.name }}</td>
              <td>{{ user.email }}</td>
              <td class="text-center">
                <span :class="'badge ' + getRoleClass(user.role)">{{ getRoleName(user.role) }}</span>
              </td>
              <td class="text-center">{{ user.group_name || '-' }}</td>
              <td class="text-nowrap text-center">
                <div class="d-flex gap-2 justify-content-center">
                  <router-link :to="`/admin/users/edit/${user.id}`" class="btn btn-warning btn-sm" style="min-width: 100px;">Редактировать</router-link>
                  <button v-if="user.role !== 'admin'" @click="deleteUser(user.id)" class="btn btn-danger btn-sm" style="min-width: 70px;">Удалить</button>
                  <div v-else style="min-width: 70px;"></div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Список групп -->
    <div v-if="showGroups" class="mt-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h3>Список групп</h3>
        <router-link to="/admin/groups/add" class="btn btn-primary">Добавить группу</router-link>
      </div>
      <div class="table-responsive">
        <table class="table table-striped table-bordered table-hover align-middle">
          <thead class="table-primary">
            <tr>
              <th style="width: 60px">ID</th>
              <th>Название группы</th>
              <th style="width: 100px">Студентов</th>
              <th style="width: 100px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="group in groups" :key="group.id">
              <td class="text-center">{{ group.id }}</td>
              <td>{{ group.name }}</td>
              <td class="text-center">{{ group.students_count }}</td>
              <td class="text-center">
                <div class="d-flex gap-1 justify-content-center">
                  <button @click="deleteGroup(group.id)" class="btn btn-danger btn-sm">Удалить</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Список курсов -->
    <div v-if="showCourses" class="mt-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h3>Список курсов</h3>
        <router-link to="/admin/courses/add" class="btn btn-primary">Добавить курс</router-link>
      </div>
      <div class="table-responsive">
        <table class="table table-striped table-bordered table-hover align-middle">
          <thead class="table-primary">
            <tr>
              <th style="width: 60px">ID</th>
              <th>Название</th>
              <th>Преподаватели</th>
              <th style="width: 80px">Уроков</th>
              <th style="width: 110px">Создан</th>
              <th style="width: 100px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="course in courses" :key="course.id">
              <td class="text-center">{{ course.id }}</td>
              <td>{{ course.title }}</td>
              <td>{{ course.teachers || '-' }}</td>
              <td class="text-center">{{ course.lessons_count || 0 }}</td>
              <td class="text-center">{{ formatDate(course.created_at) }}</td>
              <td class="text-nowrap text-center" style="min-width: 150px;">
                <div class="d-flex gap-1 justify-content-center">
                  <router-link :to="`/course/edit/${course.id}`" class="btn btn-warning btn-sm">Редактировать</router-link>
                  <button @click="deleteCourse(course.id)" class="btn btn-danger btn-sm">Удалить</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Список резервных копий -->
    <div v-if="backups.length > 0" class="mt-5">
      <h3>Резервные копии базы данных</h3>
      <div class="table-responsive">
        <table class="table table-striped table-bordered">
          <thead class="table-primary">
            <tr>
              <th>Имя файла</th>
              <th>Дата создания</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="backup in backups" :key="backup.name">
              <td>{{ backup.name }}</td>
              <td>{{ backup.date }}</td>
              <td>
                <a :href="`/api/admin/backup/download/${backup.name}`" class="btn btn-primary btn-sm">Скачать</a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '../services/api'

export default {
  name: 'AdminView',
  setup() {
    const showUsers = ref(true)
    const showGroups = ref(false)
    const showCourses = ref(false)
    
    const users = ref([])
    const groups = ref([])
    const courses = ref([])
    const stats = ref({ users: 0, groups: 0, courses: 0, teachers: 0 })
    
    const backupLoading = ref(false)
    const backups = ref([])

    const loadData = async () => {
      try {
        const [usersRes, groupsRes, coursesRes] = await Promise.all([
          api.get('/users'),
          api.get('/groups'),
          api.get('/admin/courses')
        ])
        users.value = usersRes.data
        groups.value = groupsRes.data
        courses.value = coursesRes.data
        
        stats.value = {
          users: users.value.length,
          groups: groups.value.length,
          courses: courses.value.length,
          teachers: users.value.filter(u => u.role === 'teacher').length
        }
      } catch (err) {
        console.error('Ошибка загрузки:', err)
      }
    }

    const loadBackups = async () => {
      try {
        const res = await api.get('/admin/backups')
        backups.value = res.data
      } catch (err) {
        console.error('Ошибка загрузки бэкапов:', err)
      }
    }

    const createBackup = async () => {
      backupLoading.value = true
      try {
        const res = await api.post('/admin/backup')
        if (res.data.success) {
          alert(res.data.message)
          loadBackups()
        } else {
          alert('Ошибка при создании бэкапа')
        }
      } catch (err) {
        console.error('Ошибка создания бэкапа:', err)
        alert('Ошибка при создании резервной копии')
      } finally {
        backupLoading.value = false
      }
    }

    const getRoleName = (role) => {
      const roles = { admin: 'Администратор', teacher: 'Преподаватель', student: 'Студент' }
      return roles[role] || role
    }

    const getRoleClass = (role) => {
      const classes = { admin: 'bg-danger', teacher: 'bg-primary', student: 'bg-success' }
      return classes[role] || 'bg-secondary'
    }

    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleDateString('ru-RU')
    }

    const deleteUser = async (id) => {
      if (!confirm('Удалить пользователя?')) return
      try {
        await api.delete(`/users/${id}`)
        loadData()
      } catch (err) {
        console.error('Ошибка удаления:', err)
        alert('Ошибка при удалении пользователя')
      }
    }

    const deleteGroup = async (id) => {
      if (!confirm('Удалить группу? Студенты останутся без группы.')) return
      try {
        await api.delete(`/groups/${id}`)
        loadData()
      } catch (err) {
        console.error('Ошибка удаления:', err)
        alert('Ошибка при удалении группы')
      }
    }

    const deleteCourse = async (id) => {
      if (!confirm('Удалить курс? Все уроки будут удалены.')) return
      try {
        await api.delete(`/courses/${id}`)
        loadData()
      } catch (err) {
        console.error('Ошибка удаления:', err)
        alert('Ошибка при удалении курса')
      }
    }

    onMounted(() => {
      loadData()
      loadBackups()
    })

    return {
      showUsers, showGroups, showCourses,
      users, groups, courses, stats,
      backupLoading, backups, createBackup,
      getRoleName, getRoleClass, formatDate,
      deleteUser, deleteGroup, deleteCourse
    }
  }
}
</script>