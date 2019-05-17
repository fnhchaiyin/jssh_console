# coding:UTF-8
import gl
class jgroup(object):
    def __init__(self, name='',child_groups=[], hosts = [],comment=''):
        self.name = name
        self.child_groups=child_groups
        self.hosts = hosts
        self.comment=comment
    def get_child_hosts(self):
        self.r=[]
        self.r += self.hosts
        def get_child(group):
            self.r += group.hosts
            for i in group.child_groups:
                get_child(gl.jssh['groups'][i])
        for n in self.child_groups:
            get_child (gl.jssh['groups'][n])
        h=self.r
        self.r = []
        return h
    def get_child_groups(self):
        self.r = self.child_groups
        def get_child(group):
            for i in group.child_groups:
                self.r += i.child_groups
                get_child(gl.jssh['groups'][i])
        for i in self.child_groups:
            get_child(gl.jssh['groups'][i])
        h=self.r
        self.r=''
        return h
    def __str__(self):
        self.r=''
        level=0
        self.r += "\t" * level + self.name + ':' + self.comment + "\n"
        level+=1
        for i in self.hosts:
            self.r += "\t" * level + i +':'+gl.jssh['services'][i].comment + "\n"
        def get_child(group,level):
            self.r += "\t"*level+group.name+':'+group.comment+"\n"
            level += 1
            for i in group.hosts:
                self.r += "\t" * level + i +':'+gl.jssh['services'][i].comment + "\n"
            for i in group.child_groups:
                get_child(gl.jssh['groups'][i],level)
        for group in self.child_groups:
            get_child (gl.jssh['groups'][group], level)
        r=self.r
        self.r=''
        return r