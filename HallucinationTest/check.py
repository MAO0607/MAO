import requests
import datetime
from HallucinationTest.stack import Stack  #导入栈
from HallucinationTest.tag import Tag  #导入标签类
import re
class check:
    def __init__(self,texts):
        self.ErrorList=[]#错误信息列表
        self.ActivityList=[]#活动列表（对活动重新编号）
        self.line0=[]  #未处理的语句
        self.line_tag=[]   #处理后的语句
        self.ToTag(texts)
        # for i in self.line_tag:
        #     print("spaces=",str(i.spaces)," parentheses=",i.parentheses," content=",i.content," condition=",i.condition," row=",str(i.row)," id=",i.idnum)
        self.CheckPair(self.line_tag)
        self.CheckStructure(self.line_tag)
        for i in self.ErrorList:
            print("错误： "+i)
        if len(self.ErrorList)==0:
            print("格式正确！")

    def getError(self):
        # error_prompt = ' \n'.join(self.ErrorList)
        if len(self.ErrorList)!=0:
            error_prompt=self.ErrorList[0]
        else:
            error_prompt=''
        return error_prompt

    def remove_empty_lines(self,text):  #去除奇怪的换行
            lines = text.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]#列表
            # refined_lines=[]
            # for line in non_empty_lines:
            #     num_spaces = len(line) - len(line.lstrip())#空格数量
            #     refined_lines.append((line.strip()+str(num_spaces)).replace(" ",""))
            # print(non_empty_lines)
            return non_empty_lines

    def trim_string(self,s):  #去除字符串第一个非空字符之前的空格和最后一个非空字符之后的空格
        start = 0
        end = len(s)
        # 找到第一个非空字符的位置
        for i, char in enumerate(s):
            if not char.isspace():
                start = i
                break
        # 找到最后一个非空字符的位置
        for i in range(len(s) - 1, -1, -1):
            if not s[i].isspace():
                end = i + 1
                break
        return s[start:end]

    # def extract_content_before_parentheses(self,text):  # 找到第一个左括号的索引
    #     index = text.find('(')
    #     # 如果找到了左括号
    #     if index != -1:
    #         # 返回左括号之前的内容
    #         return text[:index].strip()
    #     else:
    #         # 如果没有找到左括号，则返回 None
    #         return "none"
        
    def extract_tag_left(self,line):  #找到<到第一个空格之间的单词(左括号标签)
        # 找到第一个 "<" 的索引位置
        tag_index = line.find("<")
        
        # 找到从tag_index开始，第一个空格的索引位置
        space_index = line.find(" ", tag_index)
        
        # 提取位于tag_index和space_index之间的子字符串
        word = line[tag_index + 1:space_index]
        
        # 如果子字符串中包含英语字母，则返回这个单词，否则返回空字符串
        # english_word = ''.join(filter(str.isalpha, word))
        english_word=''.join(word)
        if english_word.isalpha():
            # print(english_word)
            return english_word
        else:
            return ""
        
    def extract_tag_right(self,line):  #找到<到第一个空格之间的单词(右括号标签)
        # 找到第一个 "<" 的索引位置
        tag_index = line.find("<")
        
        # 找到从tag_index开始，第一个空格的索引位置
        space_index = line.find(" ", tag_index)
        
        # 提取位于tag_index和space_index之间的子字符串
        word = line[tag_index + 1:space_index]
        
        # 如果子字符串中包含英语字母，则返回这个单词，否则返回空字符串
        english_word = ''.join(filter(str.isalpha, word))
        if english_word.isalpha():
            return english_word
        else:
            return ""
        
    def extract_id(self,string): #找到id里面的内容
        # 使用正则表达式匹配 id='' 中的内容
        match = re.search(r"id='([^']+)'", string)
        
        # 如果匹配成功，则返回匹配到的内容，否则返回 None
        if match:
            return match.group(1)
        else:
            return ""
        
    def extract_condition(self,string): #找到condition里面的内容
        # 使用正则表达式匹配 id='' 中的内容
        match = re.search(r"condition='([^']+)'", string)
        
        # 如果匹配成功，则返回匹配到的内容，否则返回 None
        if match:
            return match.group(1)
        else:
            return ""

    def ToTag(self,texts):#把每行都化为类结构
        non_empty_lines=self.remove_empty_lines(texts)
        for index,line in enumerate(non_empty_lines):
            spaces=len(line) - len(line.lstrip())#空格数量
            line2=self.trim_string(line) #消除空格
            self.line0.append(line2)
            # print(line2)
            if line=='<process>' or line=='</process>':
                # index=index+1
                continue

            if self.extract_tag_left(line2)=="activity":  #活动
                parentheses=''  #左右括号
                content='activity'  #标签内容
                condition=''   #条件
                idnum=self.extract_id(line2)  #id
            elif line2[0]=='<' and line2[1]!='/':  #左括号
                parentheses='<'  
                condition=self.extract_condition(line2) #条件
                tag_left=self.extract_tag_left(line2)
                # print("extract_tag_left=",tag_left)
                # line2=re.sub(r'\([^)]*\)', '',line2)
                if tag_left=='branch':  # 标签内容
                    content='branch'
                elif tag_left=='exclusiveGateway':
                    content='exclusiveGateway'
                elif tag_left=='parallelGateway':
                    content='parallelGateway'
                elif tag_left=='inclusiveGateway':
                    content='inclusiveGateway'
                else:
                    content='error'
                idnum=self.extract_id(line2)  #id

            elif line2[0]=='<' and line2[1]=='/':  #右括号
                parentheses='>'  
                tag_right=self.extract_tag_right(line2)
                if tag_right=='branch':  # 标签内容
                    content='branch'
                elif tag_right=='exclusiveGateway':
                    content='exclusiveGateway'
                elif tag_right=='parallelGateway':
                    content='parallelGateway'
                elif tag_right=='inclusiveGateway':
                    content='inclusiveGateway'
                else:
                    content='error'
                condition=''  #条件
                idnum=self.extract_id(line2)  #id
            else:
                content='error'
                parentheses=''
                condition=''
                idnum=self.extract_id(line2)  #id
            row=index+1
            self.line_tag.append(Tag(spaces,parentheses,content,condition,row,idnum))

    def CheckPair(self,line_tag):#检查配对结构（左右括号配对情况）
        stack1=Stack()
        index=0
        while index<len(line_tag):
            line=line_tag[index]
            if line.parentheses=="<" and line.content!="error":  #左括号
                stack1.push(line)  #入栈(索引,内容,条件,编号,空格数)
                index=index+1
            elif line.parentheses==">" and line.content!="error":  #右括号
                if stack1.isEmpty(): #如果栈为空
                    # print("error1")
                    self.ErrorList.append("The '</"+line.content+">' in line "+str(line.row)+" is not matched, please consider adding the matched tag in the appropriate position or removing the '</"+line.content+">' in line "+str(line.row)+".")  #错误信息
                    # self.ErrorList.append("第"+str(line.row)+"行的</"+line.content+">没有被配对，即没有<"+line.content+">，请考虑增加或删除")  #错误信息
                    index=index+1
                elif line.content==stack1.getTop().content and line.spaces==stack1.getTop().spaces: #内容匹配上了 空格数匹配上了                
                    stack1.pop()#栈中最上面的'左括号' 出栈
                    index=index+1
                else: #不匹配，浅浅分类讨论一下
                    if line.spaces<stack1.getTop().spaces:
                        # print("error2")
                        if len(stack1.getTop().condition)!=0: #存在条件
                            self.ErrorList.append("The '"+stack1.getTop().content+"' tag with id='"+stack1.getTop().idnum+"' is not matched, please consider adding the </"+stack1.getTop().content+"> in the appropriate position or removing the '"+stack1.getTop().content+"' tag with id='"+stack1.getTop().idnum+"'")  #错误信息
                            # self.ErrorList.append("The <"+stack1.getTop().content+"("+stack1.getTop().condition+")> in line "+str(stack1.getTop().row)+" is not paired (i.e., there is no </"+stack1.getTop().content+">),please consider adding the </"+stack1.getTop().content+"> in the appropriate position or removing the <"+stack1.getTop().content+"("+stack1.getTop().condition+")> in line "+str(stack1.getTop().row))  #错误信息
                            # self.ErrorList.append("第"+str(stack1.getTop().row)+"行的<"+stack1.getTop().content+"("+stack1.getTop().condition+")>没有被配对，即没有</"+stack1.getTop().content+">，请考虑增加或删除")  #错误信息
                        else:  #condition==0，有条件
                            self.ErrorList.append("The '"+stack1.getTop().content+"' tag with id='"+stack1.getTop().idnum+"' is not matched, please consider adding the </"+stack1.getTop().content+"> in the appropriate position or removing the '"+stack1.getTop().content+"' tag with id='"+stack1.getTop().idnum+"'")  #错误信息
                            
                            # self.ErrorList.append("The <"+stack1.getTop().content+"> in line "+str(stack1.getTop().row)+" is not paired (i.e., there is no </"+stack1.getTop().content+">),please consider adding the </"+stack1.getTop().content+"> in the appropriate position or removing the <"+stack1.getTop().content+"> in line "+str(stack1.getTop().row))  #错误信息
                            # self.ErrorList.append("第"+str(stack1.getTop().row)+"行的<"+stack1.getTop().content+">没有被配对，即没有</"+stack1.getTop().content+">，请考虑增加或删除")  #错误信息

                        stack1.pop()  #出栈
                        #index不变
                    else:  #line.spaces>=stack.getTop().spaces
                        # print("error3")
                        self.ErrorList.append("The </"+line.content+"> in line "+str(line.row)+" is not matched, please consider adding the matched tag in the appropriate position or removing the </"+line.content+"> in line "+str(line.row)+".")  #错误信息
                    
                        # self.ErrorList.append("The </"+line.content+"> in line "+str(line.row)+" is not paired (i.e., there is no <"+line.content+">),please consider adding the <"+line.content+"> in the appropriate position or removing the </"+line.content+"> in line "+str(line.row))  #错误信息
                        # self.ErrorList.append("第"+str(line.row)+"行的</"+line.content+">没有被配对，即没有<"+line.content+">，请考虑增加或删除")  #错误信息
                        index=index+1
                        continue  #不出栈（应该是）

            elif line.content=='activity':  #活动
                index=index+1
                continue
            else:
                self.ErrorList.append("'"+self.line0[line.row-1]+"' on line "+str(line.row)+" does not conform to the format.")  #错误信息
                
                # self.ErrorList.append("The content or tag on line "+str(line.row)+" does not conform to the format")  #错误信息
                # self.ErrorList.append("第"+str(line.row)+"行内容或标签不符合格式要求")  #错误信息
                index=index+1
        if not stack1.isEmpty():#如果栈不为空！！
            for line in stack1.items:
                # print("!!")
                self.ErrorList.append("The '"+stack1.getTop().content+"' tag with id="+stack1.getTop().idnum+"' is not matched, please consider adding the matched tag in the appropriate position or removing the '"+stack1.getTop().content+"' tag with id='"+stack1.getTop().idnum+"'.")  #错误信息  
                
                # self.ErrorList.append("The </"+line.content+"> in line "+str(line.row)+" is not matched ,please consider adding the matched tag in the appropriate position or removing the </"+line.content+"> in line "+str(line.row))  #错误信息  
                
                # self.ErrorList.append("The </"+line.content+"> in line "+str(line.row)+" is not paired (i.e., there is no <"+line.content+">),please consider adding the <"+line.content+"> in the appropriate position or removing the </"+line.content+"> in line "+str(line.row))  #错误信息  
                # self.ErrorList.append("第"+str(line.row)+"行的<"+line.content+">没有被配对，即没有</"+line.content+">，请考虑增加或删除")  #错误信息

    def CheckStructure(self,line_tag):#检查结构（分支结构、网关内结构）  建立在全部配对好的基础上
        stack2=Stack()
        index=0
        while index<len(line_tag):
            line=line_tag[index]
            # print("常规输出：",line.content,line.row,)
            if line.parentheses=="<" and line.content!="error":  #左括号
                stack2.push(line)  #入栈(索引,内容,条件,编号,空格数)
            if line.parentheses==">" and line.content!="error":  #右括号
                if not stack2.isEmpty(): #若栈为空
                    if line.content==stack2.getTop().content and line.spaces==stack2.getTop().spaces:  #配对上了
                        if line.content=="branch":  #分支
                            branch1=stack2.getTop()  #记录一下栈顶元素位置
                            if line.row==stack2.getTop().row+1:  #分支内没有活动
                                self.ErrorList.append("There is a missing activity or branch between branch or gateway with id='"+stack2.getTop().idnum+"'. Consider adding activity or branch between them or removing the tag with id='"+stack2.getTop().idnum+"'.")  #错误信息
                                
                                # self.ErrorList.append("There is a missing activity or branch between line "+str(stack2.getTop().row)+" and "+str(line.row)+". Consider adding activity between them or removing the tag in line "+str(stack2.getTop().row)+" and in line "+str(line.row))  #错误信息
                                # self.ErrorList.append("第 "+str(stack2.getTop().row)+"行和"+str(line.row)+"行之间缺少活动或分支，请考虑增加活动或删除"+stack2.getTop().content+"和"+line.content)  #错误信息
                            stack2.pop()  #出栈
                            if int(len(stack2.items))!=0 and stack2.getTop().content=="branch" and stack2.getTop().spaces==branch1.spaces-2: #栈不空且branch内直接套branch
                                self.ErrorList.append("The branch tag with id='"+branch1.idnum+"' cannot be directly nested under the branch tag with id='"+stack2.getTop().idnum+"'. Consider removing the 'branch' tag with id='"+branch1.idnum+"' and its paired branch tag, or adding a gateway outside the branch tag with id='"+branch1.idnum+"'.")  #错误信息
                                
                                # self.ErrorList.append("The '<Branch>' in line "+str(branch1)+" cannot be directly nested under the '<Branch>' in line "+str(stack2.getTop().row)+". Consider removing the 'Branch' tag in line "+str(branch1)+" and its paired branch tag, or adding a gateway outside the <Branch> tag in line "+str(branch1))  #错误信息
                                # self.ErrorList.append("第"+str(branch1)+"行的Branch不能直接套在第"+str(stack2.getTop().row)+"行的Branch下,请考虑去掉第"+str(branch1)+"行的Branch标签或增加网关")  #错误信息
                                
                        elif line.row==stack2.getTop().row+1:  #网关内没有活动
                            self.ErrorList.append("There is no activity or branch between the gateway with id='"+stack2.getTop().idnum+"'. Consider adding activity or branch between them or removing the gateway tag with id='"+stack2.getTop().idnum+"'.")  #错误信息
                            
                            # self.ErrorList.append("There is no activity or branch between <"+stack2.getTop().content+"> in line "+str(stack2.getTop().row)+" and </"+line.content+"> in line "+str(line.row)+". Consider adding activity or branch between them or removing <"+stack2.getTop().content+"> in line "+str(stack2.getTop().row)+" and </"+line.content+"> in line "+str(line.row))  #错误信息
                            # self.ErrorList.append("第"+str(stack2.getTop().row)+"行和"+str(line.row)+"行之间缺少活动或分支，请考虑增加活动或删除"+stack2.getTop().content+"和"+line.content)  #错误信息
                            stack2.pop()  #出栈
                        elif line.content=="exclusiveGateway":  #排他网关
                            i=stack2.getTop().row #索引
                            branchnum=0
                            conditionnum=0
                            while i!=line.row:
                                # print(line_tag[i-1].parentheses,line_tag[i-1].content)
                                if line_tag[i-1].parentheses=="<" and line_tag[i-1].content=='branch' and line_tag[i-1].spaces==line.spaces+2: 
                                    branchnum=branchnum+1  #分支数+1
                                    if len(line_tag[i-1].condition)!=0:
                                        conditionnum=conditionnum+1  #条件数+1
                                i=i+1
                            # print("branchnum="+branchnum,"  conditionnum="+conditionnum)
                            # print("branchnum=",branchnum)
                            if branchnum<2:
                                self.ErrorList.append("The exclusive gateway with id='"+stack2.getTop().idnum+"' is missing branch (at least two branches). Consider adding branch between the exclusive gateway with id='"+stack2.getTop().idnum+"', or changing this exclusive gateway with id='"+stack2.getTop().idnum+"' to a sequential structure.")  #错误信息
                                
                                # self.ErrorList.append("The exclusive gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" is missing branch (at least two branches). Consider adding branch between line "+str(stack2.getTop().row)+" and "+str(line.row)+", or changing this exclusive gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" to a sequential structure")  #错误信息
                                # self.ErrorList.append("第"+str(stack2.getTop().row)+"行和"+str(line.row)+"行之间的排他网关缺少分支（至少有两条分支），若无格式问题，请考虑增加分支或者去掉网关")  #错误信息
                                # "The exclusive gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" is missing branch (at least two branches). Consider adding branch between line "+str(stack2.getTop().row)+" and "+str(line.row)+", or changing the exclusive gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" to a sequential structure"
                            
                            if conditionnum!=0 and conditionnum!=branchnum:
                                self.ErrorList.append("In the exclusive gateway with id='"+stack2.getTop().idnum+"', some branches are conditional and some branches are not.It should be changed to either all conditions or none conditions.")  #错误信息
                                
                                # self.ErrorList.append("In the exclusive gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+", some branches are conditional and some branches are not. It should be changed to either all conditions or none conditions.")  #错误信息    
                                # self.ErrorList.append("第"+str(stack2.getTop().row)+"行和"+str(line.row)+"行之间的排他网关有的分支有条件，有的分支没有条件。有无条件应保持一致。")  #错误信息
                            stack2.pop()  #出栈
                        elif line.content=="parallelGateway":  #并发网关
                            i=stack2.getTop().row #索引
                            branchnum=0
                            conditionnum=0
                            while i!=line.row:
                                if line_tag[i-1].parentheses=="<" and line_tag[i-1].content=='branch' and line_tag[i-1].spaces==line.spaces+2: 
                                    branchnum=branchnum+1  #分支数+1
                                    if len(line_tag[i-1].condition)!=0:
                                        conditionnum=conditionnum+1  #条件数+1
                                i=i+1
                            if branchnum<2:
                                self.ErrorList.append("The parallel gateway with id='"+stack2.getTop().idnum+"' is missing branch (at least two branches). Consider adding branch between the parallel gateway with id='"+stack2.getTop().idnum+"', or changing this parallel gateway with id='"+stack2.getTop().idnum+"' to a sequential structure.")  #错误信息
                                
                                # self.ErrorList.append("The concurrent gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" is missing branch (at least two branches). Consider adding branch between line "+str(stack2.getTop().row)+" and "+str(line.row)+", or changing this concurrent gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" to a sequential structure")  #错误信息
                                
                                # self.ErrorList.append("第"+str(stack2.getTop().row)+"行和"+str(line.row)+"行之间的并发网关缺少分支（至少有两条分支），若无格式问题，请考虑增加分支或者去掉网关")  #错误信息
                            if conditionnum!=0:
                                self.ErrorList.append("In the parallel gateway with id='"+stack2.getTop().idnum+"', all branches cannot be conditional. Consider either set the condition='' inside the parallel gateway with id='"+stack2.getTop().idnum+"' or changing the gateway to an exclusive gateway.")  #错误信息
                                
                                # self.ErrorList.append("In the concurrent gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+", all branches cannot be conditional. Consider either removing the condition inside the concurrent gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" or changing the gateway to an exclusive gateway")  #错误信息    
                                # "In the concurrent gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+", all branches cannot be conditional. Consider either removing the condition inside the concurrent gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" or changing the gateway to an exclusive gateway"
                                # self.ErrorList.append("第"+str(stack2.getTop().row)+"行和"+str(line.row)+"行之间的并发网关中，分支不能有条件。请考虑去除条件或者修改为排他网关")  #错误信息
                            stack2.pop()  #出栈
                        elif line.content=="inclusiveGateway":  #包容网关
                            i=stack2.getTop().row #索引
                            branchnum=0
                            conditionnum=0
                            while i!=line.row:
                                # print(line_tag[i-1].parentheses,line_tag[i-1].content)
                                if line_tag[i-1].parentheses=="<" and line_tag[i-1].content=='branch' and line_tag[i-1].spaces==line.spaces+2: 
                                    branchnum=branchnum+1  #分支数+1
                                    if len(line_tag[i-1].condition)!=0:
                                        conditionnum=conditionnum+1  #条件数+1
                                i=i+1
                            if branchnum<2:
                                self.ErrorList.append("The inclusive gateway with id='"+stack2.getTop().idnum+"' is missing branch (at least two branches). Consider adding branch between the exclusive gateway with id='"+stack2.getTop().idnum+"', or changing this exclusive gateway with id='"+stack2.getTop().idnum+"' to a sequential structure.")  #错误信息
                                
                                # self.ErrorList.append("The exclusive gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" is missing branch (at least two branches). Consider adding branch between line "+str(stack2.getTop().row)+" and "+str(line.row)+", or changing this exclusive gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" to a sequential structure")  #错误信息
                                # self.ErrorList.append("第"+str(stack2.getTop().row)+"行和"+str(line.row)+"行之间的排他网关缺少分支（至少有两条分支），若无格式问题，请考虑增加分支或者去掉网关")  #错误信息
                                # "The exclusive gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" is missing branch (at least two branches). Consider adding branch between line "+str(stack2.getTop().row)+" and "+str(line.row)+", or changing the exclusive gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+" to a sequential structure"
                            
                            if conditionnum!=branchnum:
                                self.ErrorList.append("In the inclusive gateway with id='"+stack2.getTop().idnum+"', some branches do not have conditions. It should be add.")  #错误信息
                                
                                # self.ErrorList.append("In the exclusive gateway between line "+str(stack2.getTop().row)+" and "+str(line.row)+", some branches are conditional and some branches are not. It should be changed to either all conditions or none conditions.")  #错误信息    
                                # self.ErrorList.append("第"+str(stack2.getTop().row)+"行和"+str(line.row)+"行之间的排他网关有的分支有条件，有的分支没有条件。有无条件应保持一致。")  #错误信息
                            stack2.pop()  #出栈
                    else:
                        # print(line.content,stack.getTop().content,line.spaces,stack.getTop().spaces)
                        if line.spaces<stack2.getTop().spaces:
                            stack2.pop()  #出栈(没配对上的)
                            continue
                        else:
                            index=index+1
                            continue
            index=index+1
# check_instance=check(text)#创建一个类
# error=check_instance.getError()  #获取错误信息




# text="""
# <process>
#   <activity role='students' action='fill out the Association application form' objects='' id='activity1'/>
#   <activity role='club' action='Eligibility Checks' objects='Students club Application Form' id='activity2'/>
#   <exclusiveGateway id='exclusivegateway1'>
#     <branch condition='Approved' id='branch1'>
#       <activity role='' action='' objects='' id='activity3'/>
#     </branch>
#     <branch condition='Not approved' id='branch2'>
#       <activity role='students' action='modify application form' objects='Student club Application Form' id='activity4'/>
#     </branch>
#   </exclusiveGateway>
#   <parallelGateway  id='parallelgateway1'>
#     <branch id='branch3'>
#       <activity role='students' action='club interview' objects='' id='activity5'/>
#     </branch>
#     <branch id='branch4'>
#       <activity role='students' action='paying the interview fee' objects='interview fee' id='activity6'/>
#     </branch>
#   </parallelGateway>
#   <activity role='club' action='Rating' objects='Student interview results' id='activity7'/>
#   <exclusiveGateway id='exclusivegateway2'>
#     <branch condition='Rating passes' id='branch5'>
#       <activity role='Club and students' action='club orientation party' objects='cakes,gifts' id='activity8'/>
#       <activity role='students' action='participating in club activities' objects='' id='activity9'/>
#     </branch>
#     <branch condition='Failed rating' id='branch6'>
#       <activity role='students' action='failure to join the club' objects='' id='activity10'/>
#     </branch>
#   </exclusiveGateway>
# </process>
# """
# check_instance=check(text)#创建一个类
# error=check_instance.getError()  #获取错误信息

# if __name__ == "__main__":
#     ToTag(texts)
#     # for i in line_tag:
#     #     print(i.spaces,i.parentheses,i.content,i.condition,i.row)
#     CheckPair(line_tag)
#     CheckStructure(line_tag)
#     for i in ErrorList:
#         print("错误： "+i)
#     if len(ErrorList)==0:
#         print("格式正确！")