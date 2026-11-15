import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { queryClient } from '@/api/queryClient'
import { AuthProvider } from '@/auth/AuthContext'
import { RequireAuth, RequireVerified } from '@/auth/guards'
import { ToastProvider } from '@/components/toast'
import { AppLayout } from '@/layout/AppLayout'
import { ComingSoon } from '@/pages/ComingSoon'
import { ForgotPasswordPage } from '@/pages/ForgotPasswordPage'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { ResetPasswordPage } from '@/pages/ResetPasswordPage'
import { VerifyEmailPage } from '@/pages/VerifyEmailPage'
import { ThemeProvider } from '@/lib/theme'

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
                  <Route
                    path="search"
                    element={<ComingSoon title="Search" />}
                  />

                  <Route
                    path="movies"
                    element={<ComingSoon title="Movies" />}
                  />
                  <Route
                    path="movies/:id"
                    element={<ComingSoon title="Movie details" />}
                  />
                  <Route path="tv" element={<ComingSoon title="TV" />} />
                  <Route
                    path="tv/:id"
                    element={<ComingSoon title="Show details" />}
                  />
                  <Route path="anime" element={<ComingSoon title="Anime" />} />
                  <Route
                    path="anime/:id"
                    element={<ComingSoon title="Anime details" />}
                  />
                  <Route path="games" element={<ComingSoon title="Games" />} />
                  <Route
                    path="games/:id"
                    element={<ComingSoon title="Game details" />}
                  />
                  <Route
                    path="football"
                    element={<ComingSoon title="Football" />}
                  />
                  <Route
                    path="football/teams/:id"
                    element={<ComingSoon title="Team details" />}
                  />

                  <Route
                    path="dashboard"
                    element={
                      <RequireAuth>
                        <ComingSoon title="Your dashboard" />
                      </RequireAuth>
                    }
                  />
                  <Route
                    path="library"
                    element={
                      <RequireVerified>
                        <ComingSoon title="Your library" />
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
