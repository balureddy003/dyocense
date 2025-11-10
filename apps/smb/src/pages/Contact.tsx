import { Button, Paper, SimpleGrid, Stack, Text, Textarea, TextInput, Title } from '@mantine/core'
import { showNotification } from '@mantine/notifications'
import { useMutation } from '@tanstack/react-query'
import { Controller, useForm } from 'react-hook-form'

type ContactForm = {
    name: string
    company: string
    email: string
    message: string
}

export default function Contact() {
    const {
        control,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<ContactForm>({
        defaultValues: { name: '', company: '', email: '', message: '' },
    })

    const mutation = useMutation({
        mutationFn: async (values: ContactForm) => {
            await new Promise((resolve) => setTimeout(resolve, 800))
            return values
        },
        onSuccess: () => {
            showNotification({ title: 'Request received', message: 'We’ll reach out with a rollout plan shortly.', color: 'green' })
            reset()
        },
        onError: () => {
            showNotification({ title: 'Unable to send message', message: 'Please try again in a moment.', color: 'red' })
        },
    })

    const onSubmit = (values: ContactForm) => mutation.mutate(values)

    return (
        <div className="page-shell">
            <div className="glass-panel--light mx-auto max-w-3xl space-y-8">
                <Stack gap="xs">
                    <Text className="eyebrow text-brand-600">Talk to an expert</Text>
                    <Title order={2}>Design your Dyocense rollout</Title>
                    <Text c="gray.6">
                        Share a few details about your team and we’ll scope the automations, integrations, and security review you need.
                    </Text>
                </Stack>

                <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
                    <SimpleGrid cols={{ base: 1, md: 2 }}>
                        <Controller
                            control={control}
                            name="name"
                            rules={{ required: 'Name is required' }}
                            render={({ field }) => (
                                <TextInput label="Full name" placeholder="Avery Chen" error={errors.name?.message} {...field} />
                            )}
                        />
                        <Controller
                            control={control}
                            name="company"
                            rules={{ required: 'Company is required' }}
                            render={({ field }) => (
                                <TextInput label="Company" placeholder="Northwind Retail" error={errors.company?.message} {...field} />
                            )}
                        />
                    </SimpleGrid>

                    <Controller
                        control={control}
                        name="email"
                        rules={{
                            required: 'Email is required',
                            pattern: { value: /\S+@\S+\.\S+/, message: 'Enter a valid email' },
                        }}
                        render={({ field }) => (
                            <TextInput label="Work email" placeholder="ops@team.com" error={errors.email?.message} {...field} />
                        )}
                    />

                    <Controller
                        control={control}
                        name="message"
                        rules={{ required: 'Message is required' }}
                        render={({ field }) => (
                            <Textarea
                                label="What are you planning?"
                                placeholder="Product launch, GTM refresh, automation request..."
                                minRows={4}
                                error={errors.message?.message}
                                {...field}
                            />
                        )}
                    />

                    <Button type="submit" fullWidth radius="xl" loading={mutation.isPending}>
                        Request strategy session
                    </Button>
                </form>
            </div>
        </div>
    )
}
