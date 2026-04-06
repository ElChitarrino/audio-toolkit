const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '',          component: () => import('pages/IndexPage.vue') },
      { path: 'analyze',   component: () => import('pages/AnalyzePage.vue') },
      { path: 'metronome', component: () => import('pages/MetronomePage.vue') },
      { path: 'library',   component: () => import('pages/LibraryPage.vue') },
    ]
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
