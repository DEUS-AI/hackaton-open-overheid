import { Container, Title, Text, Stack } from "@mantine/core";
import { ThemeDemo } from "../../components/ThemeDemo";

export default function ThemeDemoPage() {
  return (
    <Container size="lg" py="xl">
      <Stack gap="xl">
        <div>
          <Title order={1} ta="center" mb="md">
            Government Application Theme
          </Title>
          <Text ta="center" c="dimmed" size="lg">
            A professional theme designed for government applications with accessibility and trust in mind.
          </Text>
        </div>
        <ThemeDemo />
      </Stack>
    </Container>
  );
}