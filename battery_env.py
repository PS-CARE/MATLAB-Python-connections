import gym
from gym import Env
from gym import error, spaces, utils
from gym.spaces import Discrete, Box
from gym.utils import seeding
import random
import numpy as np
import pandas as pd
import matlab.engine
'''
This is the main lib that we can use to run a matlab funciton form python code.


'''
mle = matlab.engine.start_matlab() 

class Battery_ENV(gym.Env):

    # This function is the initialisations.......
    def __init__(self):
        
        # The user define the out put voltage following by out put current we need by hard coding cause we have trained the model for this specific env...
        self.intended_out_put_current = int(22)
        self.intended_out_put_voltage = int(26)

        # I assumed that we have 3 actions associated with Duty-Cycle including: increasing, decreasing and do nothing with duty-cycle.
        self.action_space = Discrete(3)

        # I assumed only 2 observations in this case including the out put current following by out put voltage.
        self.observation_space = Box(low=float('-inf'), high=float('inf'), shape=(2,), dtype=np.float64)


        # go to reset function for more information
        self.reset()
        
        



    def step(self,action):
        '''    
         Apply action: I assume that Duty cycle is going to change by steps of 0.001
         As I mentioned it used to be changed by steps of 0.01, but I noticed we need more accuracy to obtain fine duty-cycle.
         for exp the proper duty-cycle which is working in this case study would be 0.591 but we won't be able to reach this number by steps of 0.1.
         0/100 -0.01 =-0.01 Duty-cycle
         1/100 -0.01 = 0 Duty-cycle
         2/100 -0.01 =+0.01 Duty-cycle
        '''
        reward=0
        
        self.Duty_cycle +=( (action/1000) - 0.001 )

        
        # As you suggested me I am gonna changed it to be in the range of [0.2,0.8]
        self.Duty_cycle = np.clip( self.Duty_cycle , 0.2, 0.8)

        '''
        I have attached an snap shot of my env in simulink so you can reach out to that for better understanding of the following cms.
        As I mentioned we use matlab simulink as our env
        I used matlab engine lib to be able run the matlab function which that runs the simulation for 1 sec and save the results of observation in a list.
        duty-cycle is sent to the simulation ( to the InputBlock ) then result of this duty-cycle which are current and Voltage will be send back to the python code 
        '''
        Rs_Si = mle.API(self.Duty_cycle) # Getting the response of the simulink to this specific duty-cycle!
        # that list contains all of the values of current and voltage during our simulation is running.
        
        matlab_data = Rs_Si[-100:] 
        
        #I consider the mean of last 100 values of current and voltage in that list as observations
        data_list = np.array(matlab_data).tolist()

        current_values = [entry[0] for entry in data_list]
        voltage_values = [entry[1] for entry in data_list]

        last_100_current_avg = np.mean(current_values)
        last_100_voltage_avg = np.mean(voltage_values)

        
        self.Obs_Current = round ( abs(float(last_100_current_avg)) , 2  ) # Getting the current of the simulink's response to this specific duty-cycle!
        self.Obs_Voltage = round ( abs(float(last_100_voltage_avg)) , 2  ) # Getting the voltage of the simulink's response to this specific duty-cycle!

        

        # since we our model is allowed to have only 1000 actions, after each action we take one chance...
        self.chances -= 1

        # Calculating the reward
        reward , range = self.calculate_reward()

        # Check to see whether we are done or not by chances
        done = self.check_done()

        info = {'Duty_cycle':self.Duty_cycle ,'intended_out_put_Current':self.intended_out_put_current, 'intended_out_put_Voltage':self.intended_out_put_voltage , 'Chances':self.chances}





        return np.array([self.Obs_Current, self.Obs_Voltage]) , reward , done , info


    def calculate_reward(self):
        
        

      # Calculate the reward based on the current state

      # Compute the deviation from the target current & voltage
        current_deviation = abs(self.Obs_Current  - self.intended_out_put_current)
        voltage_deviation = abs(self.Obs_Voltage - self.intended_out_put_voltage)

      # Set up Max value for error range to be accepted to get reward.
        max_current_deviation = (self.intended_out_put_current*0.03)
        max_voltage_deviation = (self.intended_out_put_voltage*0.03)


      # Define the reward function based on the deviation
        if ( current_deviation <= (max_current_deviation) ) and ( voltage_deviation <= (max_voltage_deviation) ) :
            
            reward = +1
            
        else:
            
            reward = -1

        return reward,max

    def check_done(self):

      # Determine if the episode is terminated

      if self.chances <= 0:

        return True

      else:

        return False





    def render(self):
        # Actually we do not have any visuall output so we do not need this fucntion.
        pass


    def reset(self, seed=None, options=None):
        

        '''
        As i mentioned in meeting my agent used to take a random number as duty-cycle, But I noticed that if I try to 
        find the probably suitable duty-cycle and try to keep the reset duty-cycle close to that my agent neeeds less steps
        to find out what is the that proper duty-cycle!!!!!! so that is why I came up with 0.59 as my reset duty-cycle.
        '''
        self.Duty_cycle = float(0.59)
        R = mle.API(self.Duty_cycle)
        matlab_data = R[-100:]
        data_list = np.array(matlab_data).tolist()

        current_values = [entry[0] for entry in data_list]
        voltage_values = [entry[1] for entry in data_list]

        last_100_current_avg = np.mean(current_values)
        last_100_voltage_avg = np.mean(voltage_values)

        self.Obs_Current = round ( abs(float(last_100_current_avg)) , 2  ) # Getting the current of the simulink's response to this specific duty-cycle!
        self.Obs_Voltage = round ( abs(float(last_100_voltage_avg)) , 2  ) # Getting the voltage of the simulink's response to this specific duty-cycle!

        # how many times our model can take an action to obtain the intended out put voltage.
        self.chances = 1000 # this could be probably one of those hyper!!!!!!!!!!!!!!!!!!!!!!!!!!

        return np.array([self.Obs_Current, self.Obs_Voltage])

    
    def close(self):
        pass