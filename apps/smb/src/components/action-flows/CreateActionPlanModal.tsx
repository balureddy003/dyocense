/**
 * CreateActionPlanModal - Multi-step wizard for creating action plans from recommendations
 * 
 * Steps:
 * 1. Review recommendation details
 * 2. Set timeline and priority
 * 3. Assign tasks
 * 4. Confirm and create
 */

import { useState } from 'react';
import {
    Modal,
    Button,
    Stepper,
    Group,
    TextInput,
    Textarea,
    Select,
    Stack,
    Text,
    Card,
    Badge,
    Checkbox,
    NumberInput,
} from '@mantine/core';
import { IconCheck, IconX } from '@tabler/icons-react';
import type { CoachRecommendation } from '../coach-v6/types';

interface CreateActionPlanModalProps {
    opened: boolean;
    onClose: () => void;
    recommendation: CoachRecommendation | null;
    onSubmit: (plan: ActionPlan) => void;
}

export interface ActionPlan {
    recommendationId: string;
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    dueDate: string;
    tasks: Array<{
        title: string;
        assignedTo: string;
        estimatedHours: number;
    }>;
}

export function CreateActionPlanModal({
    opened,
    onClose,
    recommendation,
    onSubmit,
}: CreateActionPlanModalProps) {
    const [active, setActive] = useState(0);
    const [planTitle, setPlanTitle] = useState('');
    const [planDescription, setPlanDescription] = useState('');
    const [priority, setPriority] = useState<'high' | 'medium' | 'low'>('medium');
    const [dueDate, setDueDate] = useState('');
    const [tasks, setTasks] = useState<Array<{ title: string; assignedTo: string; estimatedHours: number }>>([]);
    const [newTaskTitle, setNewTaskTitle] = useState('');
    const [newTaskAssignee, setNewTaskAssignee] = useState('');
    const [newTaskHours, setNewTaskHours] = useState(1);
    
    // Reset form when modal closes
    const handleClose = () => {
        setActive(0);
        setPlanTitle('');
        setPlanDescription('');
        setPriority('medium');
        setDueDate('');
        setTasks([]);
        setNewTaskTitle('');
        setNewTaskAssignee('');
        setNewTaskHours(1);
        onClose();
    };
    
    // Initialize form with recommendation data
    const initializeFromRecommendation = () => {
        if (recommendation) {
            setPlanTitle(recommendation.title);
            setPlanDescription(recommendation.description);
            setPriority(
                recommendation.priority === 'critical' ? 'high' :
                recommendation.priority === 'important' ? 'medium' : 'low'
            );
        }
    };
    
    // Add task to list
    const handleAddTask = () => {
        if (newTaskTitle.trim()) {
            setTasks([...tasks, {
                title: newTaskTitle,
                assignedTo: newTaskAssignee || 'Unassigned',
                estimatedHours: newTaskHours,
            }]);
            setNewTaskTitle('');
            setNewTaskAssignee('');
            setNewTaskHours(1);
        }
    };
    
    // Remove task from list
    const handleRemoveTask = (index: number) => {
        setTasks(tasks.filter((_, i) => i !== index));
    };
    
    // Submit action plan
    const handleSubmit = () => {
        if (!recommendation) return;
        
        const plan: ActionPlan = {
            recommendationId: recommendation.id,
            title: planTitle,
            description: planDescription,
            priority,
            dueDate,
            tasks,
        };
        
        onSubmit(plan);
        handleClose();
    };
    
    const nextStep = () => {
        if (active === 0 && !planTitle.trim()) {
            return; // Require title
        }
        setActive((current) => (current < 3 ? current + 1 : current));
    };
    
    const prevStep = () => setActive((current) => (current > 0 ? current - 1 : current));
    
    if (!recommendation) return null;
    
    // Initialize on first step
    if (active === 0 && !planTitle && opened) {
        initializeFromRecommendation();
    }
    
    return (
        <Modal
            opened={opened}
            onClose={handleClose}
            title="Create Action Plan"
            size="lg"
            padding="xl"
        >
            <Stack gap="md">
                <Stepper active={active} onStepClick={setActive}>
                    {/* Step 1: Review Details */}
                    <Stepper.Step label="Details" description="Review recommendation">
                        <Stack gap="md" mt="md">
                            <Card withBorder padding="md">
                                <Group justify="space-between" mb="xs">
                                    <Text fw={600} size="sm">Original Recommendation</Text>
                                    <Badge color={
                                        recommendation.priority === 'critical' ? 'red' :
                                        recommendation.priority === 'important' ? 'orange' : 'blue'
                                    }>
                                        {recommendation.priority}
                                    </Badge>
                                </Group>
                                <Text size="sm" c="dimmed">{recommendation.description}</Text>
                            </Card>
                            
                            <TextInput
                                label="Action Plan Title"
                                placeholder="Enter a descriptive title"
                                value={planTitle}
                                onChange={(e) => setPlanTitle(e.currentTarget.value)}
                                required
                            />
                            
                            <Textarea
                                label="Description"
                                placeholder="Describe the action plan and expected outcomes"
                                value={planDescription}
                                onChange={(e) => setPlanDescription(e.currentTarget.value)}
                                minRows={3}
                            />
                        </Stack>
                    </Stepper.Step>
                    
                    {/* Step 2: Timeline & Priority */}
                    <Stepper.Step label="Timeline" description="Set deadline and priority">
                        <Stack gap="md" mt="md">
                            <Select
                                label="Priority"
                                placeholder="Select priority"
                                value={priority}
                                onChange={(value) => setPriority(value as 'high' | 'medium' | 'low')}
                                data={[
                                    { value: 'high', label: 'High - Urgent action required' },
                                    { value: 'medium', label: 'Medium - Important but not urgent' },
                                    { value: 'low', label: 'Low - Nice to have' },
                                ]}
                            />
                            
                            <TextInput
                                label="Due Date"
                                type="date"
                                value={dueDate}
                                onChange={(e) => setDueDate(e.currentTarget.value)}
                                min={new Date().toISOString().split('T')[0]}
                            />
                            
                            <Text size="sm" c="dimmed">
                                Estimated total effort: {tasks.reduce((sum, t) => sum + t.estimatedHours, 0)} hours
                            </Text>
                        </Stack>
                    </Stepper.Step>
                    
                    {/* Step 3: Tasks */}
                    <Stepper.Step label="Tasks" description="Break down into tasks">
                        <Stack gap="md" mt="md">
                            <Group align="flex-end">
                                <TextInput
                                    label="Task Title"
                                    placeholder="e.g., Call overdue customers"
                                    value={newTaskTitle}
                                    onChange={(e) => setNewTaskTitle(e.currentTarget.value)}
                                    style={{ flex: 1 }}
                                />
                                <TextInput
                                    label="Assign To"
                                    placeholder="Name or role"
                                    value={newTaskAssignee}
                                    onChange={(e) => setNewTaskAssignee(e.currentTarget.value)}
                                    style={{ width: 150 }}
                                />
                                <NumberInput
                                    label="Hours"
                                    value={newTaskHours}
                                    onChange={(value) => setNewTaskHours(value as number)}
                                    min={0.5}
                                    max={40}
                                    step={0.5}
                                    style={{ width: 80 }}
                                />
                                <Button onClick={handleAddTask}>Add</Button>
                            </Group>
                            
                            {tasks.length === 0 ? (
                                <Text size="sm" c="dimmed" ta="center" py="xl">
                                    No tasks added yet. Add at least one task to continue.
                                </Text>
                            ) : (
                                <Stack gap="xs">
                                    {tasks.map((task, index) => (
                                        <Card key={index} withBorder padding="sm">
                                            <Group justify="space-between">
                                                <div style={{ flex: 1 }}>
                                                    <Text size="sm" fw={500}>{task.title}</Text>
                                                    <Text size="xs" c="dimmed">
                                                        {task.assignedTo} • {task.estimatedHours}h
                                                    </Text>
                                                </div>
                                                <Button
                                                    size="xs"
                                                    color="red"
                                                    variant="subtle"
                                                    onClick={() => handleRemoveTask(index)}
                                                >
                                                    Remove
                                                </Button>
                                            </Group>
                                        </Card>
                                    ))}
                                </Stack>
                            )}
                        </Stack>
                    </Stepper.Step>
                    
                    {/* Step 4: Confirm */}
                    <Stepper.Completed>
                        <Stack gap="md" mt="md">
                            <Text size="lg" fw={600}>Review & Confirm</Text>
                            
                            <Card withBorder padding="md">
                                <Stack gap="xs">
                                    <Group justify="space-between">
                                        <Text size="sm" fw={600}>Title:</Text>
                                        <Text size="sm">{planTitle}</Text>
                                    </Group>
                                    <Group justify="space-between">
                                        <Text size="sm" fw={600}>Priority:</Text>
                                        <Badge color={priority === 'high' ? 'red' : priority === 'medium' ? 'orange' : 'blue'}>
                                            {priority}
                                        </Badge>
                                    </Group>
                                    <Group justify="space-between">
                                        <Text size="sm" fw={600}>Due Date:</Text>
                                        <Text size="sm">{dueDate || 'Not set'}</Text>
                                    </Group>
                                    <Group justify="space-between">
                                        <Text size="sm" fw={600}>Tasks:</Text>
                                        <Text size="sm">{tasks.length} tasks</Text>
                                    </Group>
                                    <Group justify="space-between">
                                        <Text size="sm" fw={600}>Total Effort:</Text>
                                        <Text size="sm">{tasks.reduce((sum, t) => sum + t.estimatedHours, 0)} hours</Text>
                                    </Group>
                                </Stack>
                            </Card>
                        </Stack>
                    </Stepper.Completed>
                </Stepper>
                
                <Group justify="space-between" mt="xl">
                    <Button variant="subtle" onClick={handleClose} leftSection={<IconX size={16} />}>
                        Cancel
                    </Button>
                    
                    <Group gap="sm">
                        {active > 0 && active < 3 && (
                            <Button variant="default" onClick={prevStep}>
                                Back
                            </Button>
                        )}
                        
                        {active < 3 ? (
                            <Button
                                onClick={nextStep}
                                disabled={
                                    (active === 0 && !planTitle.trim()) ||
                                    (active === 2 && tasks.length === 0)
                                }
                            >
                                Next
                            </Button>
                        ) : (
                            <Button
                                onClick={handleSubmit}
                                leftSection={<IconCheck size={16} />}
                                color="green"
                            >
                                Create Action Plan
                            </Button>
                        )}
                    </Group>
                </Group>
            </Stack>
        </Modal>
    );
}
