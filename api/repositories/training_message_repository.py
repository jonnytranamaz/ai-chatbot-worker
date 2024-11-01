from .models import TrainingMessage

class TrainingMessageRepository:
    @staticmethod
    def save_training_message(request, response):
        training_message = TrainingMessage(request=request, response=response)
        training_message.save()
        return training_message

    @staticmethod
    def get_training_message_by_id(message_id):
        try:
            return TrainingMessage.objects.get(id=message_id)
        except TrainingMessage.DoesNotExist:
            return None

    @staticmethod
    def get_all_training_messages():
        return TrainingMessage.objects.all()