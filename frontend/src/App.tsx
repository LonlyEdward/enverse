import { QueryClientProvider } from '@tanstack/react-query'
import { lazy } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { queryClient } from '@/api/queryClient'
import { AuthProvider } from '@/auth/AuthContext'
import { RequireAuth, RequireVerified } from '@/auth/guards'
import { ToastProvider } from '@/components/toast'
import { AppLayout } from '@/layout/AppLayout'
import { ThemeProvider } from '@/lib/theme'
// The landing and login pages are the common first paint, so they stay in the
// main bundle. Every other route is a lazy chunk, loaded on first visit.
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'

// Pages use named exports; lazy() wants a default, so each loader re-maps it.
const AnimePage = lazy(() =>
  import('@/pages/AnimePage').then((m) => ({ default: m.AnimePage })),
)
const CalendarPage = lazy(() =>
  import('@/pages/CalendarPage').then((m) => ({ default: m.CalendarPage })),
)
const DashboardPage = lazy(() =>
  import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage })),
)
const DetailPage = lazy(() =>
  import('@/pages/DetailPage').then((m) => ({ default: m.DetailPage })),
)
const FootballPage = lazy(() =>
  import('@/pages/FootballPage').then((m) => ({ default: m.FootballPage })),
)
const ForgotPasswordPage = lazy(() =>
  import('@/pages/ForgotPasswordPage').then((m) => ({
    default: m.ForgotPasswordPage,
  })),
)
const GamesPage = lazy(() =>
  import('@/pages/GamesPage').then((m) => ({ default: m.GamesPage })),
)
const LibraryPage = lazy(() =>
  import('@/pages/LibraryPage').then((m) => ({ default: m.LibraryPage })),
)
const MoviesPage = lazy(() =>
  import('@/pages/MoviesPage').then((m) => ({ default: m.MoviesPage })),
)
const NotFoundPage = lazy(() =>
  import('@/pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage })),
)
const NotificationsPage = lazy(() =>
  import('@/pages/NotificationsPage').then((m) => ({
    default: m.NotificationsPage,
  })),
)
const OnboardingPage = lazy(() =>
  import('@/pages/OnboardingPage').then((m) => ({ default: m.OnboardingPage })),
)
const RecommendationsPage = lazy(() =>
  import('@/pages/RecommendationsPage').then((m) => ({
    default: m.RecommendationsPage,
  })),
)
const RegisterPage = lazy(() =>
  import('@/pages/RegisterPage').then((m) => ({ default: m.RegisterPage })),
)
const ResetPasswordPage = lazy(() =>
  import('@/pages/ResetPasswordPage').then((m) => ({
    default: m.ResetPasswordPage,
  })),
)
const SearchPage = lazy(() =>
  import('@/pages/SearchPage').then((m) => ({ default: m.SearchPage })),
)
const SettingsPage = lazy(() =>
  import('@/pages/SettingsPage').then((m) => ({ default: m.SettingsPage })),
)
const TVPage = lazy(() =>
  import('@/pages/TVPage').then((m) => ({ default: m.TVPage })),
)
const TeamDetailPage = lazy(() =>
  import('@/pages/TeamDetailPage').then((m) => ({ default: m.TeamDetailPage })),
)
const VerifyEmailPage = lazy(() =>
  import('@/pages/VerifyEmailPage').then((m) => ({ default: m.VerifyEmailPage })),
)

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <AuthProvider>
            <ToastProvider>
              <Routes>
                <Route element={<AppLayout />}>
                  <Route index element={<HomePage />} />
                  <Route path="login" element={<LoginPage />} />
                  <Route path="register" element={<RegisterPage />} />
                  <Route path="verify-email" element={<VerifyEmailPage />} />
                  <Route
                    path="forgot-password"
                    element={<ForgotPasswordPage />}
                  />
                  <Route
                    path="reset-password"
                    element={<ResetPasswordPage />}
                  />
                  <Route path="search" element={<SearchPage />} />

                  <Route path="movies" element={<MoviesPage />} />
                  <Route
                    path="movies/:id"
                    element={<DetailPage contentType="movie" />}
                  />
                  <Route path="tv" element={<TVPage />} />
                  <Route
                    path="tv/:id"
                    element={<DetailPage contentType="tv" />}
                  />
                  <Route path="anime" element={<AnimePage />} />
                  <Route
                    path="anime/:id"
                    element={<DetailPage contentType="anime" />}
                  />
                  <Route path="games" element={<GamesPage />} />
                  <Route
                    path="games/:id"
                    element={<DetailPage contentType="game" />}
                  />
                  <Route path="football" element={<FootballPage />} />
                  <Route
                    path="football/teams/:id"
                    element={<TeamDetailPage />}
                  />

                  <Route
                    path="onboarding"
                    element={
                      <RequireAuth>
                        <OnboardingPage />
                      </RequireAuth>
                    }
                  />
                  <Route
                    path="dashboard"
                    element={
                      <RequireAuth>
                        <DashboardPage />
                      </RequireAuth>
                    }
                  />
                  <Route
                    path="notifications"
                    element={
                      <RequireAuth>
                        <NotificationsPage />
                      </RequireAuth>
                    }
                  />
                  <Route
                    path="recommendations"
                    element={
                      <RequireVerified>
                        <RecommendationsPage />
                      </RequireVerified>
                    }
                  />
                  <Route
                    path="calendar"
                    element={
                      <RequireAuth>
                        <CalendarPage />
                      </RequireAuth>
                    }
                  />
                  <Route
                    path="settings"
                    element={
                      <RequireAuth>
                        <SettingsPage />
                      </RequireAuth>
                    }
                  />
                  <Route
                    path="library"
                    element={
                      <RequireVerified>
                        <LibraryPage />
                      </RequireVerified>
                    }
                  />

                  <Route path="*" element={<NotFoundPage />} />
                </Route>
              </Routes>
            </ToastProvider>
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
