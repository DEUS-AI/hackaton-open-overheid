"use client";

import {
  Button,
  Card,
  Title,
  Text,
  Badge,
  Stack,
  Group,
  Paper,
  Alert,
  TextInput,
  Notification,
  rem,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { IconCheck, IconX, IconAlertCircle, IconInfoCircle } from "@tabler/icons-react";

export function ThemeDemo() {
  const showNotification = (type: 'success' | 'error' | 'warning' | 'info') => {
    const config = {
      success: {
        title: 'Success',
        message: 'Operation completed successfully',
        color: 'govGreen',
        icon: <IconCheck style={{ width: rem(20), height: rem(20) }} />,
      },
      error: {
        title: 'Error',
        message: 'An error occurred',
        color: 'govRed',
        icon: <IconX style={{ width: rem(20), height: rem(20) }} />,
      },
      warning: {
        title: 'Warning',
        message: 'Please review this action',
        color: 'govAmber',
        icon: <IconAlertCircle style={{ width: rem(20), height: rem(20) }} />,
      },
      info: {
        title: 'Information',
        message: 'Here is some important information',
        color: 'govBlue',
        icon: <IconInfoCircle style={{ width: rem(20), height: rem(20) }} />,
      },
    };

    notifications.show(config[type]);
  };

  return (
    <Paper p="xl" shadow="sm" radius="md">
      <Stack gap="xl">
        <Title order={2} c="govBlue">Government Theme Demo</Title>
        
        {/* Color Palette */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Title order={3} mb="md">Color Palette</Title>
          <Group gap="md" mb="sm">
            <Badge color="govBlue" size="lg">Primary Blue</Badge>
            <Badge color="govGreen" size="lg">Success Green</Badge>
            <Badge color="govRed" size="lg">Error Red</Badge>
            <Badge color="govAmber" size="lg">Warning Amber</Badge>
            <Badge color="govGray" size="lg">Secondary Gray</Badge>
          </Group>
        </Card>

        {/* Buttons */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Title order={3} mb="md">Buttons</Title>
          <Group gap="md">
            <Button color="govBlue">Primary Action</Button>
            <Button variant="outline" color="govBlue">Secondary Action</Button>
            <Button variant="light" color="govGreen">Success Action</Button>
            <Button variant="filled" color="govRed">Delete Action</Button>
            <Button variant="subtle" color="govGray">Subtle Action</Button>
          </Group>
        </Card>

        {/* Alerts */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Title order={3} mb="md">Alerts</Title>
          <Stack gap="md">
            <Alert
              variant="light"
              color="govBlue"
              title="Information"
              icon={<IconInfoCircle />}
            >
              This is an informational alert with professional government styling.
            </Alert>
            <Alert
              variant="light"
              color="govGreen"
              title="Success"
              icon={<IconCheck />}
            >
              Your operation completed successfully!
            </Alert>
            <Alert
              variant="light"
              color="govAmber"
              title="Warning"
              icon={<IconAlertCircle />}
            >
              Please review this action before proceeding.
            </Alert>
            <Alert
              variant="light"
              color="govRed"
              title="Error"
              icon={<IconX />}
            >
              An error occurred. Please try again.
            </Alert>
          </Stack>
        </Card>

        {/* Form Elements */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Title order={3} mb="md">Form Elements</Title>
          <Stack gap="md">
            <TextInput
              label="Email Address"
              placeholder="Enter your email"
              required
            />
            <TextInput
              label="Government ID"
              placeholder="Enter your ID number"
              description="This information is kept confidential"
            />
          </Stack>
        </Card>

        {/* Notifications Demo */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Title order={3} mb="md">Notifications</Title>
          <Group gap="md">
            <Button 
              variant="light" 
              color="govGreen"
              onClick={() => showNotification('success')}
            >
              Show Success
            </Button>
            <Button 
              variant="light" 
              color="govRed"
              onClick={() => showNotification('error')}
            >
              Show Error
            </Button>
            <Button 
              variant="light" 
              color="govAmber"
              onClick={() => showNotification('warning')}
            >
              Show Warning
            </Button>
            <Button 
              variant="light" 
              color="govBlue"
              onClick={() => showNotification('info')}
            >
              Show Info
            </Button>
          </Group>
        </Card>

        {/* Typography */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Title order={3} mb="md">Typography</Title>
          <Stack gap="sm">
            <Title order={1}>Heading 1 - Main Title</Title>
            <Title order={2}>Heading 2 - Section Title</Title>
            <Title order={3}>Heading 3 - Subsection</Title>
            <Title order={4}>Heading 4 - Component Title</Title>
            <Text size="lg" fw={500}>Large text with medium weight</Text>
            <Text size="md">Regular paragraph text with proper line height for readability in government applications.</Text>
            <Text size="sm" c="dimmed">Small descriptive text in muted color</Text>
          </Stack>
        </Card>
      </Stack>
    </Paper>
  );
}