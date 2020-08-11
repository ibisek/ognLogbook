"""
Kalman filter.
"""


class Kalman(object):

    def __init__(self):
        self.f_1 = 1.00000
        self.q = 4.0001
        self.r = 0.20001
        self.x = 0
        self.p = 0
        self.x_last = 0
        self.p_last = 0
        self.k = 0

    def predict(self, value):
        # Predict x_temp, p_temp:
        x_temp = self.x_last
        p_temp = self.p_last + self.r

        # Update kalman values:
        self.k = (self.f_1 / (p_temp + self.q)) * p_temp
        self.x = x_temp + (self.k * (value - x_temp))
        self.p = (self.f_1 - self.k) * p_temp

        # Save this state for next time:
        self.x_last = self.x
        self.p_last = self.p

        return self.x
