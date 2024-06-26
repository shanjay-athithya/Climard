from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from datetime import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
import requests
import logging
import json

logger = logging.getLogger(__name__)

ESP32_IP = None

@csrf_exempt
def register_esp32(request):
    global ESP32_IP
    if request.method == 'POST':
        print("came")
        ESP32_IP = request.POST.get('ip')
        mac_address = request.POST.get('mac')
        logger.info(f"Received IP: {ESP32_IP}, MAC: {mac_address}")
        return JsonResponse({'status': 'IP registered', 'ip': ESP32_IP, 'mac': mac_address})
    return JsonResponse({'status': 'failed'})

def get_esp32_ip(request):
    global ESP32_IP
    if ESP32_IP:
        return JsonResponse({'status': 'success', 'ip': ESP32_IP})
    return JsonResponse({'status': 'fail', 'message': 'ESP32 IP not registered'})

def led(request):
    global ESP32_IP
    if request.method == 'POST':
        action = request.POST.get('action')
        if ESP32_IP:
            if action == 'led_on':
                response = requests.get(f"http://{ESP32_IP}/led_on")
            elif action == 'led_off':
                response = requests.get(f"http://{ESP32_IP}/led_off")
            return JsonResponse({'status': response.text})
        else:
            return JsonResponse({'status': 'ESP32 IP not registered'})
    return render(request, 'led.html')

# Global variable to store the latest sensor data
latest_sensor_data = {
    "temperature": None,
    "humidity": None,
    "ldr": None,
    "timestamp": None
}

def get_time():
    current_time = datetime.now().strftime("%H:%M:%S")
    return current_time

@csrf_exempt
def receive_data(request):
    global latest_sensor_data
    if request.method == 'POST':
        try:
            print("came")
            data = json.loads(request.body)
            latest_sensor_data['temperature'] = data['temperature']
            latest_sensor_data['humidity'] = data['humidity']
            latest_sensor_data['ldr'] = data['ldr']
            latest_sensor_data['timestamp'] = get_time()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'invalid method'}, status=405)

def home(request):
    global latest_sensor_data
    return render(request, 'home.html', {'data': latest_sensor_data})

def get_sensor_data(request):
    global latest_sensor_data
    return JsonResponse({'status': 'success', 'data': latest_sensor_data})

# Default threshold values
TEMP_THRESHOLD = 37.0
LDR_THRESHOLD = 850

@login_required
def change_thresholds(request):
    global TEMP_THRESHOLD, LDR_THRESHOLD
    
    if request.method == 'POST':
        temp_threshold = request.POST.get('temp_threshold')
        ldr_threshold = request.POST.get('ldr_threshold')
        
        # Update threshold values
        TEMP_THRESHOLD = float(temp_threshold)
        LDR_THRESHOLD = int(ldr_threshold)
        messages.success(request, "Threshold values updated successfully.")
        return redirect('change_thresholds')
    
    return render(request, 'change_thresholds.html', {
        'temp_threshold': TEMP_THRESHOLD,
        'ldr_threshold': LDR_THRESHOLD
    })

def custom_admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect('change_thresholds')  # Redirect to threshold change page
        else:
            messages.error(request, "Invalid login credentials or not an admin.")
    return render(request, 'admin_login.html')

def get_thresholds(request):
    global TEMP_THRESHOLD, LDR_THRESHOLD
    return JsonResponse({
        'temp_threshold': TEMP_THRESHOLD,
        'ldr_threshold': LDR_THRESHOLD
    })