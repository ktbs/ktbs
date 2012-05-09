#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
D'après l'article de Frédéric Le Roy dans Linux Magazine No 134.
Charge et processus : gardez votre système à l'oeil avec Python.

Se base sur le module psutil :
   - http://pypi.python.org/pypi/psutil/
   - http://code.google.com/p/psutil/

BUGs :
   - sur OSX Snow Leopard Process().get_cpu_percent() ... trigger 
     an exception psutil.error.AccessDenied
     http://code.google.com/p/psutil/issues/detail?id=108
     Simplest workaround : Launch this programm as root :/
"""

import sys
import time
import psutil

class ProcessInfo():
    """ Cette classe récupère les informations sur un prociessus.
        Utilisation CPU, consommation mémoire, etc ...
    """

    def __init__(self, pid, interval=10, callback=None):
        """Initialization de l'objet
           @param pid : identifiant du processus
           @param interval : intervalle entre la lecture des valeurs
           @param callback : fonction de rappel
        """
        # Initialisation des variables
        self.pid = None
        self._callback = callback
        self._interval = interval

        # On vérifie que le PID existe
        if not psutil.pid_exists(pid):
            print "Le processus '%s' n'existe pas" % pid
            return

        # Crée l'objet psutil
        self.p = psutil.Process(pid)
        self.pid = self.p.pid

    def start(self):
        """Récupération des informations sur le process tant que le 
           processus est en vie.
        """
        if self.pid == None:
            return

        process_loop = True
        while process_loop == True:
            # On vérifie que le processus existe toujours
            if not psutil.pid_exists(self.pid):
                print "Le processus '%s' n'existe plus : on arrête sa " \
                      "surveillance" % self.pid
                process_loop = False
                continue

            # On récupère les valeurs et on les donne à la fonction de 
            # rappel
            values = self.get_values()
            self._callback(self.pid, values)
            time.sleep(self._interval)

    def get_values(self):
        """Récupération des valeurs intéressantes et stockage dans
           un dictionnaire.
        """
        cpu_percent = round(self.p.get_cpu_percent(), 1)
        # récupération des informations en mémoire et conversion en Mo
        memory_total_phymem = round(psutil.TOTAL_PHYMEM / (1024 * 1024), 0)
        memory_info = self.p.get_memory_info()
        memory_rss = round(memory_info[0] / (1024 * 1024), 1)
        memory_vsz =  round(memory_info[1] / (1024 * 1024), 1)
        memory_percent = round(self.p.get_memory_percent(), 1)
        values = {"pid": self.pid,
                  "cpu_percent": cpu_percent,
                  "memory_total_phymem": memory_total_phymem,
                  "memory_rss": memory_rss,
                  "memory_vsz": memory_vsz,
                  "memory_percent": memory_percent,
                  }

        return values

def display(pid, data):
    """Fonction de rappel pour tester la classe ProcessInfo.
    """
    print "DATA (%s) = %s" % (pid, str(data))

if __name__ == "__main__":
    # Instanciation de la classe pour test
    my_process = ProcessInfo(int(sys.argv[1]), 15, display)
    my_process.start()
