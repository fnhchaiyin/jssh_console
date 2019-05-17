import sys, time
class ProgressBar:
    def __init__(self,total = 100, width = 50):
        self.count = 0
        self.total = total
        self.width = width
    def move(self):
        self.count += 1
    def show(self):
        sys.stdout.write(' ' * (self.width + 9) + '\r')
        sys.stdout.flush()
        progress = self.width * self.count / self.total
        sys.stdout.write('{0:3}/{1:3} :'.format(self.count, self.total))
        sys.stdout.write('#' * progress + '-' * (self.width - progress) + '\r')
        if progress == self.width:
            sys.stdout.write('\n')
        sys.stdout.flush()

# bar = ProgressBar(total=20)
# for i in range(10):
#     bar.move()
#     bar.show()
#     time.sleep(1)
