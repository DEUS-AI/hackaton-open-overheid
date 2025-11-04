# Tools

## Service Bus Publisher

```python
  publisher = ServiceBusPublisher(CONNECTION_STRING, QUEUE_NAME)

  # Publish one message
  message_data = {
      "id": "msg-001",
      "timestamp": "2025-08-06T10:00:00Z",
      "event_type": "data_update",
      "source": "dutch_government_system",
      "data": {
          "citizen_id": "123456789",
          "municipality": "Amsterdam",
          "action": "address_change",
          "details": {
              "old_address": "Old Street 1, 1000 AA Amsterdam",
              "new_address": "New Street 2, 1001 BB Amsterdam",
          },
      },
  }

  success = publisher.publish_message(
      message_content=message_data,
      subject="citizen_data_update",
      custom_properties={
          "municipality": "Amsterdam",
          "priority": "high",
          "version": "1.0",
      },
  )

  if success:
    logger.info("Single message published successfully")


  batch_messages = []
  for i in range(5):
      msg = {
          "id": f"batch-msg-{i:03d}",
          "timestamp": "2025-08-06T10:00:00Z",
          "event_type": "batch_data",
          "source": "dutch_government_system",
          "data": {
              "record_id": f"rec-{i:03d}",
              "municipality": f"City-{i}",
              "action": "batch_update",
          },
      }
      batch_messages.append(msg)

  success = publisher.publish_batch_messages(batch_messages)

  if success:
      logger.info("Batch messages published successfully")
```

## Service Bus Consumer

```python
  # Example 1: Get queue information
  queue_info = consumer.get_queue_info()
  if queue_info:
      logger.info(f"Queue '{QUEUE_NAME}' info:")
      logger.info(f"  - Active messages: {queue_info['active_message_count']}")
      logger.info(
          f"  - Dead letter messages: {queue_info['dead_letter_message_count']}"
      )
      logger.info(f"  - Size: {queue_info['size_in_bytes']} bytes")

  # Example 2: Start continuous listening (uncomment to enable)
  logger.info("\n--- Starting continuous listening ---")
  logger.info("Press Ctrl+C to stop")
  consumer.start_continuous_listening(process_message)
```
