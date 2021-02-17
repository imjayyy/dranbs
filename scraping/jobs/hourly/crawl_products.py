from django_extensions.management.jobs import HourlyJob


class Job(HourlyJob):
    help = "crawling products job"

    def execute(self):
        print()
        pass
