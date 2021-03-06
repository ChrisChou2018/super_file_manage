from django.shortcuts import render
import os
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from common.Define import RETURN_CODE
from django.core import serializers
import shutil
import json
from concurrent.futures import ThreadPoolExecutor
from file_manage import models
from django import forms
from django.contrib.auth.models import Permission
from file_manage.check_per import check_permission
from django.contrib.auth.decorators import login_required
# Create your views here.


base_dir = settings.BASE_DIR
media_base_dir = os.path.join(base_dir, 'media')



@check_permission
@login_required
def request_file_tree(request):
    if request.method == "GET":
        GET = request.GET.get
        file_id = GET('id')
        data_list = []
        file_path = None
        if file_id == "#":
            file_path = media_base_dir
            file_list = os.listdir(media_base_dir)
            file_list.reverse()
        else:
            file_path = GET('file_path')
            file_path = file_path.replace('#',media_base_dir)
            file_list = os.listdir(file_path)
            file_list.reverse()
        for i in file_list:
            file_abs_dir = os.path.join(file_path, i)
            if os.path.isdir(file_abs_dir):
                data_list.append({'id':os.path.join(file_path, i),
                                  'text':i,
                                  "children":True,
                                  'icon':'/static/file_manage/jstree/ico/file.ico'})
        return JsonResponse(data_list,safe=False)




@check_permission
@login_required
def create_dir(request):
    if request.method == "POST":
        POST = request.POST.get
        file_path = POST('file_path')
        file_path = file_path.replace('#',media_base_dir)
        if os.path.exists(file_path):
            file_path += '1'
        if os.path.basename(file_path) == "New node":
            file_path += '1'
        os.makedirs(file_path)
        dir_name = os.path.basename(file_path)
        return JsonResponse({'dir_name':dir_name,'id':file_path})



@check_permission
@login_required
def rename_dir(request):
    if request.method == "POST":
        POST = request.POST.get
        file_path = POST('file_path')
        old_file_path = POST('old_file_path')
        new_file_name = POST('new_file_name')
        if new_file_name:
            file_path = os.path.join(os.path.dirname(old_file_path),new_file_name)
        if file_path and "#" in file_path:
            file_path = file_path.replace('#', media_base_dir)
        if old_file_path and "#" in old_file_path:
            old_file_path = old_file_path.replace('#', media_base_dir)
        if os.path.exists(old_file_path):
            os.renames(old_file_path,file_path)
        dir_name = os.path.basename(file_path)
        return JsonResponse({'dir_name':dir_name,'id':file_path})



@check_permission
@login_required
def delete_dir(request):
    if request.method == "POST":
        file_path_list = request.POST.getlist('file_path[]')
        for file_path in file_path_list:
            file_path = file_path.replace('#', media_base_dir)
            if os.path.exists(file_path):
                if os.path.basename(file_path) == "root":
                    return JsonResponse({'return_code':'SUCCESS'})
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
        return JsonResponse({'return_code':'SUCCESS'})



@check_permission
@login_required
def request_file_list(request):
    file_type_dict = {
        "png": "glyphicon glyphicon-picture",
        "PNG": "glyphicon glyphicon-picture",
        "JPG" : "glyphicon glyphicon-picture",
        "jpg" : "glyphicon glyphicon-picture",
        "txt": "glyphicon glyphicon-book",
        "mp4": "glyphicon glyphicon-film",
        "ts": "glyphicon glyphicon-film",
        "dir": "glyphicon glyphicon-folder-open",
        "other" : "glyphicon glyphicon-question-sign",
    }
    file_type_image = {
        "txt": "/static/file_manage/image/file_image/text.png",
        "mp4": "/static/file_manage/image/file_image/video.png",
        "ts": "/static/file_manage/image/file_image/video.png",
        "dir": "/static/file_manage/image/file_image/file.png",
        "other" : "/static/file_manage/image/file_image/other.png",
    }
    if request.method == "GET":
        GET = request.GET.get
        file_path = GET('file_path')
        file_path = file_path.replace('/', os.sep)
        if file_path.startswith('#'):
            file_path = file_path.replace('#', media_base_dir)
        
        data = {
            'li_ele':'',
            'div_ele':'',
        }
        li_ele = """
        <li class="list-group-item file_item" file_type="{0}" file_path="{1}" file_server_path="{2}">
            <span class="{3}"></span> {4}
        </li>
        """
        div_ele = """
        <div class="col-xs-6 col-md-3 file_item" file_type="{0}" file_path="{1}" file_server_path="{2}" style="max-height: 130px;overflow: hidden;white-space: nowrap;text-overflow: ellipsis;">
            <a class="thumbnail" style="text-align: center;">
            <img src="{3}" alt="..." style="max-height: 80px;">
            {4}
            </a>
        </div>
        """
        if os.path.exists(file_path):
            file_list = os.listdir(file_path)
            for i in file_list:
                file_abs_dir = os.path.join(file_path, i)
                file_server_dir = file_abs_dir.replace(base_dir, '').replace('\\', '/')
                if os.path.isdir(file_abs_dir):
                    data['li_ele'] += li_ele.format("dir", file_abs_dir, '', file_type_dict['dir'], i)
                    data['div_ele'] += div_ele.format("dir", file_abs_dir, '', file_type_image['dir'], i)
                elif '.' in i and i.split('.')[1] in file_type_dict:
                    if i.split('.')[1] in ['mp4','ts',]:
                        data['li_ele'] += li_ele.format(i.split('.')[1], file_abs_dir, file_server_dir, file_type_dict[i.split('.')[1]], i)
                        data['div_ele'] += div_ele.format(i.split('.')[1], file_abs_dir, file_server_dir, file_type_image[i.split('.')[1]], i)
                    elif i.split('.')[1] in ['png', 'JPG', 'jpg', 'PNG']:
                        data['li_ele'] += li_ele.format(i.split('.')[1], file_abs_dir, file_server_dir, file_type_dict[i.split('.')[1]], i)
                        data['div_ele'] += div_ele.format(i.split('.')[1], file_abs_dir, file_server_dir, file_server_dir, i)
                    else:
                        data['li_ele'] += li_ele.format(i.split('.')[1], file_abs_dir, file_server_dir, file_type_dict[i.split('.')[1]], i)
                        data['div_ele'] += div_ele.format(i.split('.')[1], file_abs_dir, file_server_dir, file_type_image[i.split('.')[1]], i)
                else:
                     data['li_ele'] += li_ele.format("other", file_abs_dir, file_server_dir, file_type_dict['other'], i)
                     data['div_ele'] += div_ele.format("other", file_abs_dir, file_server_dir, file_type_image['other'], i)
        return JsonResponse(data)




def write_file(file_path, file_obj):
        with open(file_path, 'wb')as w:
            for chunk in file_obj.chunks():
                w.write(chunk)


@check_permission
@login_required
def add_files(request):
    return_value = {
        'return_code':RETURN_CODE.SUCCESS,
        'return_msg':'',
        'datas':'',
    }
    try:
        FILES = request.FILES
        POST = request.POST.get
        file_dir_name = POST('file_path')
        with ThreadPoolExecutor(max_workers=10) as pool:
            for k, v in FILES.items():
                w_file_path = os.path.join(file_dir_name, k)
                pool.submit(write_file, **{'file_path':w_file_path, 'file_obj':v})
        return JsonResponse(return_value)

    except Exception as error:
        return_value['return_code'] = RETURN_CODE.FAIL
        return_value['return_msg'] = "服务器出错，错误：{0}".format(error)
        return JsonResponse(return_value)



def request_page_mode(request):
    page_mode = None
    if request.method == 'GET':
        with open(base_dir+'/static/file_manage/page_conf.json', 'r')as f:
            page_mode = json.load(f)
        return JsonResponse({'data':page_mode})
    else:
        mode = request.POST.get('mode')
        with open(base_dir+'/static/file_manage/page_conf.json', 'w')as f:
            json.dump({'page_mode':mode}, f)
        return JsonResponse({})



@check_permission
@login_required
def mv_dir(request):
    if request.method == 'POST':
        file_path_list = request.POST.getlist('file_path_list[]')
        new_path = request.POST.get('new_path')
        new_path = new_path.replace('#', media_base_dir)
        for i in file_path_list:
            i = i.replace('#', media_base_dir)
            i = i.replace('/', os.sep)
            if new_path == os.path.dirname(i):
                continue
            try:
                shutil.move(i, new_path)
            except shutil.Error:
                return JsonResponse({'return_code':RETURN_CODE.FAIL, 'return_msg':'移动失败，可能路径已存在'})
        return JsonResponse({'return_code':RETURN_CODE.SUCCESS})



@check_permission
@login_required
def request_user_list(request):
    if request.method == 'GET':
        user_info = models.UserInfo.objects.values()
        tr_ele = '<button type="button" class="list-group-item user_item" user_id={0}>{1}</button>'
        tr_data = ''
        for i in user_info:
            tr_data += tr_ele.format(i['id'], i['first_name'] if i['first_name'] else i['username'])
        return JsonResponse({'data':tr_data})



def request_permission_list(request):
    if request.method == 'GET':
        permission_list = models.UserInfo._meta.permissions
        op_data = []
        for i in permission_list:
            op_data.append({"value":i[0], "text":i[1],})
        return JsonResponse({'data':op_data})



class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = models.UserInfo
        fields = ('id', 'email', 'username', 'first_name', 'is_superuser', 'is_staff', 'is_active')

    def clean_password2(self):
		# Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2


    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user




@check_permission
@login_required
def create_user(request):
    return_value = {
        "return_code" : RETURN_CODE.SUCCESS,
        "return_msg"  : "",
        "datas"       : None,
        }
    if request.method == 'POST':
        o = UserCreationForm(request.POST)
        permission_list = request.POST.get('permission_list[]')
        if permission_list:
            permission_list = permission_list.split(',')
        if not o.is_valid():
            return_value["return_code"] = RETURN_CODE.INVALID_PARAMS
            return_value['return_msg'] = "参数无效"
            return JsonResponse(return_value)
        else:
            user_obj = o.save()
            if permission_list and permission_list[0] != 'null':
                for i in permission_list:
                    per_obj = Permission.objects.filter(codename=i).first()
                    user_obj.user_permissions.add(per_obj.id)
            return JsonResponse(return_value)



class Form_UpdateUser(forms.Form):
    id = forms.IntegerField()
    is_active = forms.BooleanField(required=False)
    is_superuser = forms.BooleanField(required=False)
    first_name = forms.CharField(max_length=32, required=False)
    username = forms.CharField(max_length=32, required=False)

    def clean_username(self):
        obj = models.UserInfo.objects.filter(username=self.cleaned_data['username']).exists()
        if obj:
            raise forms.ValidationError("当前用户名已经存在")
        return self.cleaned_data['username']




@check_permission
@login_required
def update_user(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        user_obj = models.UserInfo.objects.filter(id=user_id).values().first()
        permission_obj = models.UserInfo.objects.filter(id=user_id).first().user_permissions.all()
        permission_list = [i.codename for i in permission_obj]
        return JsonResponse({'data':user_obj, 'permission_list':permission_list,})
    else:
        o = Form_UpdateUser(request.POST)
        permission_list = request.POST.get('permission_list[]', None)
        if permission_list:
            permission_list = permission_list.split(',')
        if not o.is_valid():
            return JsonResponse({'return_code':RETURN_CODE.FAIL, 'return_msg':'参数错误{0}'.format(o.errors)})
        else:
            cleaned_data = o.cleaned_data
            new_data = {k:v for k, v in cleaned_data.items() if k in request.POST}
            qs_obj = models.UserInfo.objects.filter(id=new_data.get('id'))
            user_obj = qs_obj.first()
            if permission_list[0] != 'null':
                per_obj = Permission.objects.filter(codename__in=permission_list).values_list('id')
                per_id_list = [i[0] for i in per_obj]
                user_obj.user_permissions.set(per_id_list)
            else:
                user_obj.user_permissions.clear()
            qs_obj.update(**new_data)
            return JsonResponse({'return_code':RETURN_CODE.SUCCESS})



@check_permission
@login_required
def delete_user(request):
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            qs_obj = models.UserInfo.objects.filter(id=user_id)
            qs_obj.delete()
            return JsonResponse({'return_code':RETURN_CODE.SUCCESS})
        except Exception as error:
            return JsonResponse({'return_code':RETURN_CODE.FAIL, 'return_msg':'删除失败，服务器出错:{0}'.format(error)})




class Form_ChangePassword(forms.Form):
    password1 = forms.CharField(max_length=32, required=False)
    password2 = forms.CharField(max_length=32, required=False)

    def clean_password2(self):
		# Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2



@check_permission
@login_required
def change_password(request):
    if request.method == "POST":
        o = Form_ChangePassword(request.POST)
        if not o.is_valid():
            return JsonResponse({'return_code':RETURN_CODE.FAIL, 'return_msg':'两次密码不一致'})
        else:
            user_id = request.POST.get('id')
            qs_obj = models.UserInfo.objects.filter(id=user_id)
            data = o.cleaned_data
            password = data['password2']
            if not password:
                return JsonResponse({'return_code':RETURN_CODE.FAIL, 'return_msg':'密码不能为空'})
            else:
                qs_obj.first().set_password(password)
                qs_obj.first().save()
                return JsonResponse({'return_code':RETURN_CODE.SUCCESS})


