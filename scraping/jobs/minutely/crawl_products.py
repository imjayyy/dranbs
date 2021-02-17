from django_extensions.management.jobs import MinutelyJob


class Job(MinutelyJob):
    help = "crawling products job"

    def execute(self):
        print("hello world")
