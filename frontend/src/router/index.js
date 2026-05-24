import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import AdminView from '../views/AdminView.vue'
import CourseView from '../views/CourseView.vue'
import GroupView from '../views/GroupView.vue'
import AssignmentView from '../views/AssignmentView.vue'
import GradeView from '../views/GradeView.vue'
import CreateCourseView from '../views/CreateCourseView.vue'
import AddGroupsToCourseView from '../views/AddGroupsToCourseView.vue'
import AddLessonView from '../views/AddLessonView.vue'
import TakeTestView from '../views/TakeTestView.vue'
import AddUserView from '../views/AddUserView.vue'
import EditUserView from '../views/EditUserView.vue'
import AddGroupView from '../views/AddGroupView.vue'
import AddCourseView from '../views/AddCourseView.vue'
import EditCourseView from '../views/EditCourseView.vue'

const routes = [
  { path: '/login', component: LoginView, meta: { requiresAuth: false } },
  { path: '/', component: HomeView, meta: { requiresAuth: true } },
  { path: '/admin', component: AdminView, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/course/:id', component: CourseView, meta: { requiresAuth: true } },
  { path: '/course/:courseId/group/:groupId', component: GroupView, meta: { requiresAuth: true } },
  { path: '/lesson/:lessonId/group/:groupId', component: AssignmentView, meta: { requiresAuth: true, role: 'student' } },
  { path: '/grade/lesson/:lessonId/group/:groupId', component: GradeView, meta: { requiresAuth: true, role: 'teacher' } },
  { path: '/create-course', component: CreateCourseView, meta: { requiresAuth: true, role: 'teacher' } },
  { path: '/course/:id/add-groups', component: AddGroupsToCourseView, meta: { requiresAuth: true, role: 'teacher' } },
  { path: '/course/:courseId/group/:groupId/add-lesson', component: AddLessonView, meta: { requiresAuth: true, role: 'teacher' } },
  { path: '/test/lesson/:lessonId/group/:groupId', component: TakeTestView, meta: { requiresAuth: true, role: 'student' } },
  { path: '/admin/users/add', component: AddUserView, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/users/edit/:id', component: EditUserView, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/groups/add', component: AddGroupView, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/courses/add', component: AddCourseView, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/course/edit/:id', component: EditCourseView, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userData = localStorage.getItem('user')
  const user = userData ? JSON.parse(userData) : null

  if (to.meta.requiresAuth && !user) {
    next('/login')
  } else if (to.meta.role && (!user || user.role !== to.meta.role)) {
    next('/')
  } else if (to.path === '/login' && user) {
    if (user.role === 'admin') {
      next('/admin')
    } else {
      next('/')
    }
  } else {
    next()
  }
})

export default router