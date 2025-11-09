import { MantineProvider } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactElement } from 'react'
import { render } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'

export const renderWithProviders = (ui: ReactElement) => {
    const queryClient = new QueryClient()
    return render(
        <QueryClientProvider client={queryClient}>
            <MantineProvider>
                <BrowserRouter>{ui}</BrowserRouter>
            </MantineProvider>
        </QueryClientProvider>,
    )
}
