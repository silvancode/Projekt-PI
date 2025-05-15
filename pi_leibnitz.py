import time
import math

def calc_pi_sum(max_iteration):
    k = 1
    sum = 0
    for i in range(max_iteration):
        sum = sum + (-1 if (i%2) else +1)*4/k
        k = k+2
    return sum

def relativ_error(measured_value):
    return 100* (math.pi - measured_value)/measured_value
 
def calc_pi_sum_power_10(max_iteration):
    k = 1
    sum = 0
    exponent = 0
    t = time.process_time_ns()
    for i in range(max_iteration):

        sum = sum + (-1 if (i%2) else +1)*4/k
        k = k+2
        if (i%10**exponent)==0:
            exponent = exponent + 1
            elapsed_time = (time.process_time_ns() - t)*1e-9
            diff = math.pi - sum
            quotient = sum/math.pi
            rel_error = relativ_error(sum)
            #print(f"exponent: {exponent:3d} k: {k:12d} elapsed sec: {elapsed_time:7.5f} sumpi: {sum:22.20f} diff: {diff:^ 22.20f} quotient: {quotient:^22.20f} rel. error {rel_error:^ 22.20f}%")
            t = time.process_time_ns()
    exponent = exponent + 1
    elapsed_time = (time.process_time_ns() - t)*1e-9
    diff = math.pi - sum
    quotient = sum/math.pi
    rel_error = relativ_error(sum)
    #print(f"exponent: {exponent:3d} k: {k:12d} elapsed sec: {elapsed_time:7.5f} sumpi: {sum:22.20f} diff: {diff:^ 22.20f} quotient: {quotient:^22.20f} rel. error {rel_error:^ 22.20f}%")
    return sum


# def calc_pi_sum_array(start_iteration, max_iteration):
# #    sums = [0] * 10 
#     sums_index = 0
#     sums = [0]
#     k = 1

#     for i in range(0,10**i,start_iteration_to_power_ten):
#         sum = sum + (-1 if (i%2) else +1)*4/k
#         k = k+2
#         sums.append(sum)

#     for i in range(start_iteration_to_power_ten, max_iteration_to_power_ten):
#         sum = sums[sums_index]
#         for i in range(10**i,10**(i+1)):
#             sum = sum + (-1 if (i%2) else +1)*4/k
#             k = k+2
#             sums.append(sum)
# 1 s
# s s+1
# s+1 s+2


# for i in range(6,12):
#     k = 10**i
#     t = time.process_time()
#     sum = calc_pi_sum(k)
#     elapsed_time = time.process_time() - t
#     diff = math.pi - sum
#     quotient = sum/math.pi
#     print(f"i: {i:3d} k: {k:20d} elapsed sec: {elapsed_time:20.1f} sumpi: {sum:22.20f} diff: {diff:22.20f} quotient: {quotient:22.20f}")

# def calc_precision(diff):
#     i = 0
#     while (diff*10**i)%10 != 0:
#         i=i+1
#     return i



