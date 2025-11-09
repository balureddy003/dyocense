import { config, list } from '@keystone-6/core'
import { password, relationship, select, text, timestamp } from '@keystone-6/core/fields'

export default config({
    server: {
        port: 3001,
        cors: { origin: ['http://localhost:5178', 'http://localhost:3000'], credentials: true },
    },
    db: {
        provider: 'sqlite',
        url: 'file:./keystone.db',
    },
    lists: {
        User: list({
            fields: {
                name: text({ validation: { isRequired: true } }),
                email: text({ validation: { isRequired: true }, isIndexed: 'unique' }),
                password: password(),
                tenant: relationship({ ref: 'Tenant.users' }),
            },
        }),
        Tenant: list({
            fields: {
                name: text({ validation: { isRequired: true }, isIndexed: 'unique' }),
                users: relationship({ ref: 'User.tenant', many: true }),
                workspaces: relationship({ ref: 'Workspace.tenant', many: true }),
                createdAt: timestamp({ defaultValue: { kind: 'now' } }),
            },
        }),
        Workspace: list({
            fields: {
                name: text({ validation: { isRequired: true } }),
                tenant: relationship({ ref: 'Tenant.workspaces' }),
                projects: relationship({ ref: 'Project.workspace', many: true }),
                createdAt: timestamp({ defaultValue: { kind: 'now' } }),
            },
        }),
        Project: list({
            fields: {
                title: text({ validation: { isRequired: true } }),
                description: text(),
                workspace: relationship({ ref: 'Workspace.projects' }),
                status: select({
                    options: [
                        { label: 'Draft', value: 'draft' },
                        { label: 'Active', value: 'active' },
                        { label: 'Completed', value: 'completed' },
                    ],
                    defaultValue: 'draft',
                }),
                createdAt: timestamp({ defaultValue: { kind: 'now' } }),
            },
        }),
    },
})
