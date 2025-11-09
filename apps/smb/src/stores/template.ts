import { create } from 'zustand'
import { BusinessTemplate, templates } from '../data/templates'

type TemplateState = {
    selectedTemplate: BusinessTemplate
    setTemplate: (id: string) => void
}

export const useTemplateStore = create<TemplateState>((set) => ({
    selectedTemplate: templates[0],
    setTemplate: (id: string) =>
        set(() => {
            const template = templates.find((t) => t.id === id) ?? templates[0]
            return { selectedTemplate: template }
        }),
}))
