def AudioIn(r, sr, source):
    try:
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source)
        userinput = r.recognize_google(audio)
        return userinput
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
        return ""
    except sr.UnknownValueError:
        print("unknown error occurred")
        return ""


def AudioOut(engine, command):
    engine.say(command)
    engine.runAndWait()
