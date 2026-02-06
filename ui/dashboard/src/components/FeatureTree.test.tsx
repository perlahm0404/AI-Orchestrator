/**
 * Test FeatureTree component for hierarchical work queue view.
 *
 * TDD: These tests are written BEFORE the implementation.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FeatureTree } from './FeatureTree'

// Mock hierarchy data
const mockHierarchyData = {
  epics: [
    {
      id: 'EPIC-001',
      name: 'User Authentication',
      description: 'Complete OAuth implementation',
      status: 'in_progress',
      features: [
        {
          id: 'FEAT-001',
          name: 'Google OAuth',
          priority: 0,
          status: 'in_progress',
          tasks: [
            {
              id: 'TASK-001',
              description: 'Implement OAuth flow',
              status: 'completed',
              retry_budget: 15,
              retries_used: 2
            },
            {
              id: 'TASK-002',
              description: 'Add callback handler',
              status: 'in_progress',
              retry_budget: 15,
              retries_used: 5
            }
          ]
        },
        {
          id: 'FEAT-002',
          name: 'GitHub OAuth',
          priority: 1,
          status: 'pending',
          tasks: [
            {
              id: 'TASK-003',
              description: 'Setup GitHub app',
              status: 'pending',
              retry_budget: 15,
              retries_used: 0
            }
          ]
        }
      ]
    }
  ]
}

describe('FeatureTree', () => {
  describe('Rendering', () => {
    it('should render epic nodes', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      expect(screen.getByText('User Authentication')).toBeInTheDocument()
    })

    it('should render feature nodes', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      expect(screen.getByText('Google OAuth')).toBeInTheDocument()
      expect(screen.getByText('GitHub OAuth')).toBeInTheDocument()
    })

    it('should render task nodes', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      expect(screen.getByText(/Implement OAuth flow/)).toBeInTheDocument()
      expect(screen.getByText(/Add callback handler/)).toBeInTheDocument()
      expect(screen.getByText(/Setup GitHub app/)).toBeInTheDocument()
    })

    it('should show priority badges for features', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      // P0, P1 badges should be visible
      expect(screen.getByText(/P0/)).toBeInTheDocument()
      expect(screen.getByText(/P1/)).toBeInTheDocument()
    })
  })

  describe('Collapsible Nodes', () => {
    it('should start with epics expanded by default', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      // Features should be visible (epic is expanded)
      expect(screen.getByText('Google OAuth')).toBeInTheDocument()
    })

    it('should collapse epic when clicked', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      const epicNode = screen.getByText('User Authentication')
      fireEvent.click(epicNode)

      // Features should be hidden (epic collapsed)
      expect(screen.queryByText('Google OAuth')).not.toBeInTheDocument()
    })

    it('should expand epic when clicked again', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      const epicNode = screen.getByText('User Authentication')

      // Collapse
      fireEvent.click(epicNode)
      expect(screen.queryByText('Google OAuth')).not.toBeInTheDocument()

      // Expand
      fireEvent.click(epicNode)
      expect(screen.getByText('Google OAuth')).toBeInTheDocument()
    })

    it('should collapse feature nodes', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      const featureNode = screen.getByText('Google OAuth')
      fireEvent.click(featureNode)

      // Tasks should be hidden
      expect(screen.queryByText(/Implement OAuth flow/)).not.toBeInTheDocument()
    })
  })

  describe('Progress Bars', () => {
    it('should show progress bar for epic', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      // Epic has 1 completed task out of 3 total = 33%
      const progressBar = screen.getByRole('progressbar', { name: /epic progress/i })
      expect(progressBar).toBeInTheDocument()
    })

    it('should show progress bar for features', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      // Feature 1 has 1/2 tasks completed = 50%
      const progressBars = screen.getAllByRole('progressbar', { name: /feature progress/i })
      expect(progressBars.length).toBeGreaterThan(0)
    })

    it('should calculate correct progress percentage for epic', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      // 1 completed / 3 total = 33.33%
      expect(screen.getByText(/33%/)).toBeInTheDocument()
    })

    it('should calculate correct progress percentage for feature', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      // Google OAuth: 1/2 = 50%
      expect(screen.getByText(/50%/)).toBeInTheDocument()
    })
  })

  describe('Status Color Coding', () => {
    it('should apply pending status color', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      const pendingTask = screen.getByText(/Setup GitHub app/)
      expect(pendingTask.className).toContain('text-gray')
    })

    it('should apply in_progress status color', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      const inProgressTask = screen.getByText(/Add callback handler/)
      expect(inProgressTask.className).toContain('text-blue')
    })

    it('should apply completed status color', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      const completedTask = screen.getByText(/Implement OAuth flow/)
      expect(completedTask.className).toContain('text-green')
    })

    it('should apply blocked status color', () => {
      const blockedData = {
        epics: [{
          id: 'EPIC-001',
          name: 'Test',
          status: 'blocked',
          features: [{
            id: 'FEAT-001',
            name: 'Blocked Feature',
            status: 'blocked',
            priority: 0,
            tasks: [{
              id: 'TASK-001',
              description: 'Blocked task',
              status: 'blocked',
              retry_budget: 15,
              retries_used: 0
            }]
          }]
        }]
      }

      render(<FeatureTree data={blockedData} />)

      const blockedTask = screen.getByText(/Blocked task/)
      expect(blockedTask.className).toContain('text-red')
    })
  })

  describe('Task Details', () => {
    it('should call onTaskClick when task is clicked', () => {
      const onTaskClick = vi.fn()
      render(<FeatureTree data={mockHierarchyData} onTaskClick={onTaskClick} />)

      const task = screen.getByText(/Implement OAuth flow/)
      fireEvent.click(task)

      expect(onTaskClick).toHaveBeenCalledWith({
        id: 'TASK-001',
        description: 'Implement OAuth flow',
        status: 'completed',
        retry_budget: 15,
        retries_used: 2
      })
    })

    it('should show retry information in task details', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      // Task with retries_used should show it
      expect(screen.getByText(/2\/15/)).toBeInTheDocument() // retries_used/retry_budget
    })
  })

  describe('Empty States', () => {
    it('should show empty message when no epics', () => {
      render(<FeatureTree data={{ epics: [] }} />)

      expect(screen.getByText(/No work queue data/i)).toBeInTheDocument()
    })

    it('should handle epic with no features', () => {
      const emptyData = {
        epics: [{
          id: 'EPIC-001',
          name: 'Empty Epic',
          status: 'pending',
          features: []
        }]
      }

      render(<FeatureTree data={emptyData} />)

      expect(screen.getByText('Empty Epic')).toBeInTheDocument()
      expect(screen.getByText(/No features/i)).toBeInTheDocument()
    })
  })

  describe('Real-time Updates', () => {
    it('should update when data prop changes', () => {
      const { rerender } = render(<FeatureTree data={mockHierarchyData} />)

      expect(screen.getByText('User Authentication')).toBeInTheDocument()

      // Update data
      const updatedData = {
        epics: [{
          id: 'EPIC-002',
          name: 'Updated Epic',
          status: 'pending',
          features: []
        }]
      }

      rerender(<FeatureTree data={updatedData} />)

      expect(screen.getByText('Updated Epic')).toBeInTheDocument()
      expect(screen.queryByText('User Authentication')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      expect(screen.getByRole('tree')).toBeInTheDocument()
    })

    it('should support keyboard navigation', () => {
      render(<FeatureTree data={mockHierarchyData} />)

      const epicNode = screen.getByText('User Authentication')

      // Should collapse on Enter key
      fireEvent.keyDown(epicNode, { key: 'Enter' })
      expect(screen.queryByText('Google OAuth')).not.toBeInTheDocument()

      // Should expand on Enter key
      fireEvent.keyDown(epicNode, { key: 'Enter' })
      expect(screen.getByText('Google OAuth')).toBeInTheDocument()
    })
  })
})
