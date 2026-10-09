import type { ReactElement } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"

interface RenderAppOptions {
  route?: string
}

export function renderApp(
  ui: ReactElement,
  { route = "/" }: RenderAppOptions = {},
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}
