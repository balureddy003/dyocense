import { Container } from '@mantine/core'
import { OnboardingChecklist } from '../components/OnboardingChecklist'
import DashboardFixed from './DashboardFixed'

export default function Home() {
    const hasCompletedOnboarding = typeof window !== 'undefined' && localStorage.getItem('dyocense_onboarding_dismissed') === 'true'
    return (
        <Container size="xl" className="py-6">
            {!hasCompletedOnboarding ? <OnboardingChecklist /> : <DashboardFixed />}
        </Container>
    )
}
