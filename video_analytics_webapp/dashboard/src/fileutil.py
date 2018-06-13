class FileUtil:
    @staticmethod
    def join(*paths):
        str=""
        for index,path in enumerate(paths):
            str = str + path +'/'
        return str[:-1]

