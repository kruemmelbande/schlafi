#this is a discord bot which besides having varíous commands, can send a custom message to a channel at a certain time
import discord, json, random, time, datetime, os, asyncio,requests
compmode=0
cversion=1.2
try:
    import psutil
    from gpiozero import CPUTemperature
except:
    compmode=1

#test uwu
client=discord.Client()
# load settings

def getsettings(fp):
    global token, prefix, default_quotes, bot_channel, update_pending, default_wake, wake_channel, settings, sversion, last_known_quote, cucom
    settings = json.load(fp)
    token = settings["token"]
    prefix = settings["prefix"]
    default_quotes = settings["default_quotes"]
    bot_channel = settings["bot-channel"]
    update_pending = settings["update-pending"]
    default_wake = settings["default-wake"]
    wake_channel = settings["wake-channel"]
    sversion=settings["version"]
    last_known_quote=settings["last-known-quote"]
    cucom=settings["custom-commands"]
    print("The bot has been started at "+str(datetime.datetime.now()))
    print("--settings--")
    print(settings)

def command(target,message,bot=0):
    global postcommand
    if message.content.startswith(prefix+target):
        #cut off the prefix and target
        if len(message.content)>len(prefix+target):
            postcommand=message.content[len(prefix+target):]
            if postcommand[0]==" " and len(postcommand)>1:
                postcommand=postcommand[1:]
        else:
            postcommand=""

        if bot:#if the command is supposed to be only accesed in the bot channel
            return message.channel.id==bot_channel
        return 1

    else:
        return 0

def loadsettings():
    global settings, token, prefix, default_quotes, bot_channel, update_pending, default_wake, wake_channel, updatemode
    try:
        updatemode=0
        with open('settings.json') as fp:
                getsettings(fp)
    except:
        try:
            with open('settings.json') as fp:
                updatemode=1
                #get only token bot-channel and prefix
                settings = json.load(fp)
                token = settings["token"]
                bot_channel = settings["bot-channel"]
                prefix = settings["prefix"]
        except Exception:
            with open('defaults.json') as fp:
                print("!!!DEFAULTS LOADED!!!")
                print("THIS WILL NOT WORK!")
                getsettings(fp)


def savesettings():
    global settings, quote
    try:
        settings["last-known-quote"]=quote
    except:
        settings["last-known-quote"]="Quote not found"
    with open('settings.json', 'w') as fp:
        json.dump(settings, fp)
        print("settings.json saved")
        #print(settings)
sendnow=0
loadsettings()
if cucom:
    try:
        from custom import on_rdy, on_msg
    except:
        print("custom commands not found")
        cucom=0
        pass
sendtime=default_wake.split(":")

@client.event
async def on_ready():
    global botchan,bot_channel,updatemode,bot_channel
    if updatemode:
        
        botchan=client.get_channel(id=int(bot_channel))
        await botchan.send("The bot has been started in update mode. Please provide a valid settings.json file. (!restore)")
    else:
        global wakechan, wake_channel,sversion,quote,starttime
        botchan=client.get_channel(id=int(bot_channel))
        wakechan=client.get_channel(id=int(wake_channel))
        await botchan.send("Bot logged in!")
        starttime=datetime.datetime.now()
        if compmode:
            await botchan.send("Bot is running in compatability mode. Some commands may not work.")
        if cversion!=sversion:
            await botchan.send(f"The bot has been updated to version {cversion} from {sversion}!")
            settings["version"]=cversion
        quote=last_known_quote
        print("Bot logged in!")
        savesettings()
        if cucom:
            on_rdy()


async def quotesend():#this is the function which sends the quote at the right time
    await client.wait_until_ready()
    await asyncio.sleep(10)
    global quote, sendtime,sendnow, last_known_quote

    while not client.is_closed():
        now=datetime.datetime.now()
        if (now.hour==int(sendtime[0]) and now.minute==int(sendtime[1])) or sendnow==1:
            sendnow=0
            print("sending quote")
            await wakechan.send(str( quote))
            quote=random.choice(default_quotes)
            print("quote sent")
            await asyncio.sleep(61)
        else:
            await asyncio.sleep(1)
            print(now.hour,"|",now.minute,"|", now.second, "\t|", sendtime[0],"|",sendtime[1],end="\r")



commands=["help","quote","settime","send","exit","reminder","cancel","reboot","bash","backup","restore","addquote","listquotes","removequote","gethwinfo","addnote","removenote","getnote"]
@client.event
async def on_message(message):
    global settings,sendtime, cancel,default_quotes, sendnow,starttime
    if message.author==client.user:
        return
    if updatemode:
        if command("restore",message,1):#restores the settings.json file from the bot channel
            await botchan.send("Restoring backup...")
            settings=requests.get(message.attachments[0].url).json()
            savesettings()
            loadsettings()
            await botchan.send("Backup restored. Please restart the bot to exit update mode.")
            return
        if command("reboot",message,1):
            await botchan.send("Rebooting...")
            os.system("sudo reboot")
            time.sleep(5)
            print("How did I get here? (couldnt reboot)")
    if command("help",message):
        out="```"
        for comms in commands:
            out+=prefix+comms+"\n"
        out+="```"
        await message.channel.send(out)
    if command("quote",message,1):
        global quote
        quote=postcommand
        await botchan.send(message.content+" | Quote set to: "+quote)
#        await message.delete()
    if command("settime",message):
        global sendtime
        sendtime=postcommand.split(":")
        sendtime[0]=int(sendtime[0])
        sendtime[1]=int(sendtime[1])
        await botchan.send(message.content+" | Time set to: "+str(sendtime[0]).zfill(2)+":"+str(sendtime[1]).zfill(2))
#        await message.delete()
        settings["default-wake"]=str(sendtime[0])+":"+str(sendtime[1])
        savesettings()
    if command("send",message):
        sendnow=1
        await message.delete()
    if command("exit",message):
        if int(bot_channel)==int(message.channel.id):
            if postcommand.startswith("yes im sure"):
                await botchan.send("Shutting down...")
                await client.logout()
                await client.close()
                exit()
            else:
                await botchan.send("Are you sure you want to exit? Type '!exit yes im sure' to confirm.")
#                await message.delete()
    if command("reminder",message):

        cancel=0
        tmp=postcommand.split(":")
        if len(tmp)==3:
            await message.channel.send("Reminder set for "+str(tmp[0])+":"+str(tmp[1])+"\nMessage: "+tmp[2])
            now=datetime.datetime.now()
            while now.hour!=int(tmp[0]) or now.minute!=int(tmp[1]):
                now=datetime.datetime.now()
                await asyncio.sleep(5)
                if cancel==1:
                    break
            if cancel==0:
                await wakechan.send(tmp[2])
        else:
            await message.channel.send("Invalid format. Please use 'hh:mm:reminder' and do not use ':' in the reminder.")
        #await message.delete()
    if command("cancel",message):

        cancel=1
        await message.channel.send("Reminder cancelled.")
    if command("reboot",message,1):
        await botchan.send("Rebooting...")
        os.system("sudo reboot")#only works on linux, if no sudo password is set. This is intended for the raspberry pi, which by default has no password to access sudo.
    if command("bash",message,1):#BIG DANGEROUS, USE AT YOUR OWN RISK
        await botchan.send("Bash command: "+postcommand)
        os.system(postcommand)
        await botchan.send("Command executed.")
    if command("backup",message,1):#sends the settings.json file to the bot channel
        await botchan.send("Sending backup...")
        savesettings()
        await botchan.send(file=discord.File("settings.json"))
    if command("restore",message,1):#restores the settings.json file from the bot channel
        await botchan.send("Restoring backup...")
        settings=requests.get(message.attachments[0].url).json()
        savesettings()
        loadsettings()
        await botchan.send("Backup restored.")
    if command("addquote",message,1):

        default_quotes.append(postcommand)
        await botchan.send("Quote added.")
        savesettings()
    if command("listquotes",message,1):

        out="```"
        n=0
        for quote in default_quotes:
            out+=str(n)+": "+quote+"\n"
            n+=1
        out+="```"
        await botchan.send(out)
    if command("removequote",message,1):
        index=int(postcommand)
        if index<len(default_quotes):
            del default_quotes[index]
            await botchan.send("Quote removed.")
            savesettings()
        else:
            await botchan.send("Invalid index.")
    if command("gethwinfo",message,1):
        try:
            #get the average CPU load of the last 5 seconds
            await botchan.send("Getting hardware info...")
            load=[]
            for i in range(10):
                await asyncio.sleep(0.5)
                load.append(CPUTemperature().temperature)
            load=sum(load)/len(load)
            #get the hardware info of the raspberry pi
            out="```"
            out+="CPU Temp: "+str(round(load,2))+"C\n"
            out+="CPU Usage: "+str(psutil.cpu_percent())+"%\n"
            out+="RAM Usage: "+str(psutil.virtual_memory().percent)+"%\n"
            out+="```"
            await botchan.send(out)
        except:
            await botchan.send("Error getting hardware info.")
    if command("addnote",message,0):
        notename=postcommand.split(" ")[0]
        settings["notes"][notename]=postcommand.split(" ")[1:]
        savesettings()
        await message.channel.send("Note added.")
    if command("removenote",message,0):
        notename=postcommand
        if notename == "*":
            settings["notes"]={}
            savesettings()
            await botchan.send("All notes removed.")
        if notename in settings["notes"]:
            del settings["notes"][notename]
            savesettings()
            await message.channel.send("Note removed.")
        else:
            await message.channel.send("Note not found.")

    if command("getnote",message,0):
        notename=postcommand
        if notename in settings["notes"]:
            out="```"
            for note in settings["notes"][notename]:
                out+=note+"\n"
            out+="```"
            await message.channel.send(out)
        else:
            await message.channel.send("Note not found.")
    if command("info",message,1):
        out="```"
        uptime=datetime.datetime.now()-starttime
        out+="Uptime: "+str(uptime.days)+" days, "+str(uptime.seconds//3600)+" hours, "+str(uptime.seconds//60%60)+" minutes, "+str(uptime.seconds%60)+" seconds\n"
        out+="Bot version: "+str(cversion)+"\n"
        out+="Bot channel: "+str(bot_channel)+"\n"
        out+="Wake channel: "+str(wake_channel)+"\n"
        out+="```"
        await botchan.send(out)
    if cucom:
        on_msg(message, botchan, wakechan, prefix, settings)
if not updatemode:
    client.loop.create_task(quotesend())
client.run(token)