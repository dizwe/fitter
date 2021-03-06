from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from .models import Person, TopClothes, BottomClothes, SizeInfo, SameClothes, SingleDataList
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.formsets import formset_factory, BaseFormSet
import json
from .forms import PersonForm, TopClothesForm, BottomClothesForm, SameClothesForm,\
                   CriteriaBottomForm,  CriteriaTopForm

def index(request):
    # reverse 는 url 하드코딩 피할수 있도록 해줌
    return render(request, 'fitterKakao/index.html')


def make_question_generator(whole_d):
    # data 과부하 줄이기
    for sex in ['man','woman']:
        shw_filtered_sizes = whole_d[sex]
        height_key = list(shw_filtered_sizes.keys())
        height_key = list(map(int, height_key))  # 원래 문자니까
        weight_range = range(15, 152) if sex =='man' else range(15, 105)
        for height in range(min(height_key), max(height_key)+10, 10):
            for weight in weight_range: # 해보니 그렇던데?/여자
                yield sex, height, weight


def read_json(fname, encoder):
    with open(fname, encoding=encoder) as data_file:
        json_data = json.load(data_file)
    return json_data


@user_passes_test(lambda u: u.is_superuser)
def data_add(request):
    file_path = os.path.join(settings.STATIC_ROOT, 'json/question_tree.json')
    question_tree = read_json(file_path, 'utf8')
    for sex, height, weight in make_question_generator(question_tree):
        print(sex, height, weight)
        parameters_data = question_tree[sex][str(height)][str(weight)]  # 자료가 있어야함
        try:
            if parameters_data:  # 데이터가 있다면
                size_info = SizeInfo(sex=sex, height=int(height), weight=int(weight))
                parameter_list = ['shoulder', 'chest', 'arm', 'waist',
                                  'bottom_waist', 'crotch', 'thigh', 'length', 'hem', 'hip',
                                  'crotch_height', 'middle_thigh', 'knee', 'calf', 'nipple']
                for parameter in parameter_list:
                    setattr(size_info, parameter, parameters_data[parameter])  # get attr

                size_info.save()
        except KeyError as e:
            continue

    return HttpResponse("DONE")


@user_passes_test(lambda u: u.is_superuser)
def data_del(request):
    SizeInfo.objects.all().delete()
    return HttpResponse("DEL DONE")


def size_list_to_dict(suggested_size):
    param_list = ['shoulder', 'chest', 'arm', 'waist',
                  'bottom_waist', 'crotch', 'thigh', 'length', 'hem', 'hip',
                  'crotch_height', 'middle_thigh', 'knee', 'calf', 'nipple']

    each_par_dict = {}
    for i, size in enumerate(suggested_size):
        each_par_dict[param_list[i]] = size
    return each_par_dict


def anticipate_size(user_name):
    """개인 답변으로 사이즈 추정하기"""
    person = Person.objects.filter(name=user_name)
    # 나중에 이거 [0]하는 부분 바꿔야함!
    person_info_dict = person.values('sex', 'height', 'weight', 'shoulder_a', 'chest_a', 'sleeve_a', 'waist_a',
                                     'hip_a', 'crotch_a', 'length_a', 'thigh_a', 'hem_a')[0]  # queryset
    # 키는 1770 이런 형식으로 되어있으므로 10 곱해야함
    user_sex = person_info_dict['sex']
    user_height, user_weight = person_info_dict['height'] * 10, person_info_dict['weight']

    # ['shoulder', 'chest', 'arm', 'waist'
    # 'bottom_waist', 'crotch', 'thigh', 'length', 'hem', 'hip',
    # 'crotch_height', 'middle_thigh', 'knee', 'calf', 'nipple'] 순서 질문지
    question = []
    for answer in ['shoulder_a', 'chest_a', 'sleeve_a', 'waist_a',
                   'waist_a', 'crotch_a', 'thigh_a', 'length_a', 'hem_a', 'hip_a',
                   'length_a', 'thigh_a', '', '', 'chest_a']:
        if len(answer) == 0:
            question.append(1)
        else:
            question.append(person_info_dict[answer])

    """DB 에서 데이터 찾기"""
    suggested_size_filter = \
        SizeInfo.objects.filter(sex=user_sex).filter(height=user_height).filter(weight=user_weight)

    """예상 사이즈 추천하고 실측 데이터로 바꾸기"""
    parameter_list = ['shoulder', 'chest', 'arm', 'waist',
                      'bottom_waist', 'crotch', 'thigh', 'length', 'hem', 'hip',
                      'crotch_height', 'middle_thigh', 'knee', 'calf', 'nipple']

    suggested_size = []
    for parameter, q in zip(parameter_list, question):
        # size info 에서 신체 부위별로 데이터 얻어오기
        parameter_dict = suggested_size_filter.values(parameter).first()[parameter]
        # 데이터가 dict 형식이므로 dict 로 바꾸기
        parameter_dict = json.loads(parameter_dict.replace("'", '"'))
        suggested_size.append(parameter_dict[str(q)])

    suggested_size = size_list_to_dict(suggested_size)

    return suggested_size

@login_required
def suppose_size(request, kinds, tag_num):
    try:
        person = Person.objects.filter(name=request.user)
        suggested_size = anticipate_size(request.user)

        if kinds == 'top':
            clothes = TopClothes.objects.filter(pk=tag_num)  # POST 한 정보만 보게?(일단 그냥 하나만 보게 하자)

        elif kinds == 'bot':
            clothes = BottomClothes.objects.filter(pk=tag_num)  # POST 한 정보만 보게?(일단 그냥 하나만 보게 하자)

    except TopClothes.DoesNotExist or BottomClothes.DoesNotExist:
        raise Http404("Data does not exist")

    return render(request, 'fitterKakao/result.html', {'types' : kinds,
                                                       'clothes': clothes,
                                                       'person': person,
                                                       'suggest_size': suggested_size, })


def check_data(d):
    exist = SizeInfo.objects.filter(sex=d['sex']).filter(height=d['height']*10).filter(weight=d['weight']).exists()

    return exist


@login_required
def post_new(request):
    if request.method == "POST": # 이미 보낸거라면
        person_form = PersonForm(request.POST)

        if person_form.is_valid(): # 저장된 form 형식이 잘 맞는지
            if not check_data(person_form.cleaned_data): # 없는 데이터라면,
                sex_filtered = SizeInfo.objects.filter(sex=person_form.cleaned_data['sex'])
                return render(request, 'fitterKakao/no_data.html', {'sex_filtered':sex_filtered,})

            person = person_form.save(commit=False) # False 바로 저장하지는 마
            person.name = request.user
            person.save()
            return redirect('fitterKakao:choose_clothes')
    else:
        person_form = PersonForm()

    return render(request, 'fitterKakao/post_new.html', {'person_form': person_form,})


@login_required
def post_edit(request, user_name):
    if not user_name == request.user.username:
        return render(request, 'fitterKakao/index.html')
    try:
        existing_data = Person.objects.get(name__username=user_name)
    except Person.DoesNotExist:
        return redirect('fitterKakao:post_new')

    if request.method == "POST":  # 이미 보낸거라면
        person_form = PersonForm(request.POST, instance=existing_data)
        if person_form.is_valid(): # 저장된 form 형식이 잘 맞는지
            if not check_data(person_form.cleaned_data): # 없는 데이터라면,
                sex_filtered = SizeInfo.objects.filter(sex=person_form.cleaned_data['sex'])
                return render(request, 'fitterKakao/no_data.html', {'sex_filtered':sex_filtered,})
            person = person_form.save(commit=False) # False 바로 저장하지는 마
            person.name = request.user
            person.save()
            return redirect('fitterKakao:choose_clothes')
    else:
        person_form = PersonForm(instance=existing_data)

    return render(request, 'fitterKakao/post_new.html', {'person_form': person_form, })


@login_required
def add_clothes(request, kinds):
    """한꺼번에 여러 옷들까지 추가할수 있는 기능(공통된 부분은 same_clothes 로)"""
    class RequiredFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            super(RequiredFormSet, self).__init__(*args, **kwargs)
            for form in self.forms:
                form.empty_permitted = False

    top_clothes_formset = formset_factory(TopClothesForm, max_num=3,
                                          formset=RequiredFormSet)
    bottom_clothes_formset = formset_factory(BottomClothesForm, max_num=3,
                                             formset=RequiredFormSet)

    if request.method == "POST":
        # 공통되는 부분 form
        same_clothes_form = SameClothesForm(request.POST, request.FILES)
        if kinds == 'top':
            clothes_formset = top_clothes_formset(request.POST, request.FILES)
            hashTag = '#top-clothes'
        elif kinds == 'bot':
            clothes_formset = bottom_clothes_formset(request.POST, request.FILES)
            hashTag = '#bottom-clothes'

        if clothes_formset.is_valid():
            same_clothes = same_clothes_form.save(commit=False)
            same_clothes.save()
            just_saved = SameClothes.objects.get(pk=same_clothes.pk)

            for form in clothes_formset.forms:
                clothes = form.save(commit=False)
                clothes.nick = just_saved
                clothes.url = just_saved
                clothes.photo = just_saved
                clothes.name = request.user
                clothes.save()

            return redirect('fitterKakao:suppose_size', kinds=kinds, tag_num=clothes.id)
    else:
        same_clothes_form = SameClothesForm()
        if kinds == 'top':
            clothes_formset = top_clothes_formset()
        elif kinds == 'bot':
            clothes_formset = bottom_clothes_formset()

    return render(request, 'fitterKakao/add_clothes.html', {'types' : kinds,
                                                            'clothes_formset': clothes_formset,
                                                            'same_clothes_form': same_clothes_form,})


@login_required
def edit_clothes(request, kinds, tag_num):
    # 데이터 내거인지 확인
    if kinds == 'top':
        dataName = TopClothes.objects.filter(pk=tag_num).values('name__username').first()['name__username']
        hashTag = '#top-clothes'
    elif kinds == 'bot':
        dataName = BottomClothes.objects.filter(pk=tag_num).values('name__username').first()['name__username']
        hashTag = '#bottom-clothes'
    if not dataName == request.user.username:
        return render(request, 'fitterKakao/index.html')

    if request.method == "POST":
        same_clothes_form = SameClothesForm(request.POST, request.FILES)

        if kinds == 'top':
            existing_clothes = TopClothes.objects.get(pk=tag_num)
            clothes_form = TopClothesForm(request.POST, request.FILES, instance=existing_clothes)
        elif kinds == 'bot':
            existing_clothes = BottomClothes.objects.get(pk=tag_num)
            clothes_form = BottomClothesForm(request.POST, request.FILES, instance=existing_clothes)
        if clothes_form.is_valid():
            same_clothes = same_clothes_form.save(commit=False)
            same_clothes.save()
            just_saved = SameClothes.objects.get(pk=same_clothes.pk)

            clothes = clothes_form.save(commit=False)
            clothes.nick = just_saved
            clothes.url = just_saved
            if 'same_photo-stay' not in request.POST: # 사진을 유지하라고 하지 않았으면
                clothes.photo = just_saved
            clothes.name = request.user
            clothes.save()

            return redirect(reverse('fitterKakao:choose_clothes')+hashTag)
    else:
        # pk는 TopClothes밖에 없으므로 그 저장된 데이터의 foreignkey pk를 다시 구해야함
        if kinds == 'top':
            existing_clothes = TopClothes.objects.get(pk=tag_num)
            clothes_form = TopClothesForm(instance=existing_clothes)
        elif kinds == 'bot':
            existing_clothes = BottomClothes.objects.get(pk=tag_num)
            print(type(existing_clothes))
            clothes_form = BottomClothesForm(instance=existing_clothes)
        # 이미 있는 데이터의 foreignkey pk 구하기
        existing_same = SameClothes.objects.get(pk=existing_clothes.nick.pk)
        same_clothes_form = SameClothesForm(instance=existing_same)

    return render(request, 'fitterKakao/edit_clothes.html', {'types' : kinds,
                                                             'clothes_form': clothes_form,
                                                             'same_clothes_form': same_clothes_form,})


@login_required
def choose_clothes(request):
    """데이터 없으면 옷장이 아니라 데이터 입력으로 들어가기"""
    try:
        _ = Person.objects.get(name__username=request.user.username)
    except Person.DoesNotExist:
        return redirect('fitterKakao:post_new')

    top_clothes = TopClothes.objects.filter(name=request.user)
    bottom_clothes = BottomClothes.objects.filter(name=request.user)

    return render(request, 'fitterKakao/clothes.html', {'top_clothes': top_clothes,
                                                        'bottom_clothes': bottom_clothes, })


def delete_clothes(request, kinds, tag_num):
    if kinds == 'top':
        hashTag = '#top-clothes'
        clothes = TopClothes.objects.filter(pk=tag_num)  # POST 한 정보만 보게?(일단 그냥 하나만 보게 하자)
    elif kinds == 'bot':
        hashTag = '#bottom-clothes'
        clothes = BottomClothes.objects.filter(pk=tag_num)  # POST 한 정보만 보게?(일단 그냥 하나만 보게 하자)

    clothes.delete()
    return redirect(reverse('fitterKakao:choose_clothes')+hashTag)


def single_mode(request):
    return render(request, 'fitterKakao/single/single_mode.html')


def is_from_other(dict_data, kinds, past_url):
    top_param = ['size', 'top_length', 'shoulder', 'chest', 'sleeve']
    bottom_param = ['size', 'waist', 'bot_length', 'hip', 'crotch', 'thigh', 'hem']
    clothes_param = top_param if kinds == "top" else bottom_param

    same = {}
    same['same_nick'] = dict_data.get('same_nick', 'Untitled')
    # 타사이트에서 왔다면 url 값이 저장될거다
    same['same_url'] = past_url
    clothes = {key: dict_data.get(key, 0) for key in clothes_param}
    if clothes['size'] == 0:
        clothes['size'] = 'FREE'

    return same, clothes


def single_post_body(request, kinds):
    if request.method == "POST": #이미 보낸거라면
        person_form = PersonForm(request.POST)
        same_clothes_form = SameClothesForm(request.POST)
        if kinds == 'top':
            clothes_form = TopClothesForm(request.POST)
        elif kinds == 'bot':
            clothes_form = BottomClothesForm(request.POST)

        if person_form.is_valid() and clothes_form.is_valid() and same_clothes_form.is_valid(): # 저장된 form 형식이 잘 맞는지
            single_person_dict = person_form.cleaned_data
            single_clothes_dict = clothes_form.cleaned_data
            same_clothes_dict = same_clothes_form.cleaned_data
            clothes_nick = same_clothes_dict['same_nick']
            clothes_link = same_clothes_dict['same_url']

            if not check_data(single_person_dict): # 없는 데이터라면,
                sex_filtered = SizeInfo.objects.filter(sex=person_form.cleaned_data['sex'])
                return render(request, 'fitterKakao/no_data.html', {'sex_filtered':sex_filtered,})

            # ['shoulder', 'chest', 'arm', 'waist'
            # 'bottom_waist', 'crotch', 'thigh', 'length', 'hem', 'hip',
            # 'crotch_height', 'middle_thigh', 'knee', 'calf', 'nipple'] 순서
            question = []
            for answer in ['shoulder_a', 'chest_a', 'sleeve_a', 'waist_a',
                           'waist_a', 'crotch_a', 'thigh_a', 'length_a', 'hem_a', 'hip_a',
                           'length_a', 'thigh_a', '', '', 'chest_a']:
                if len(answer) == 0:
                    question.append(1)
                else:
                    question.append(single_person_dict[answer])

            user_sex = single_person_dict['sex']
            user_height = single_person_dict['height']*10
            user_weight = single_person_dict['weight']
            """데이터 찾기"""
            suggested_size_filter = \
                SizeInfo.objects.filter(sex=user_sex).filter(height=user_height).filter(weight=user_weight)

            """개인의 데이터"""
            parameter_list = ['shoulder', 'chest', 'arm', 'waist',
                              'bottom_waist', 'crotch', 'thigh', 'length', 'hem', 'hip',
                              'crotch_height', 'middle_thigh', 'knee', 'calf', 'nipple']

            """예상 사이즈 추천하고 실측 데이터로 바꾸기"""

            suggested_size = []
            for parameter, q in zip(parameter_list, question):
                parameter_dict = suggested_size_filter.values(parameter).first()[parameter]
                parameter_dict = json.loads(parameter_dict.replace("'", '"'))
                suggested_size.append(parameter_dict[str(q)])

            suggested_size = size_list_to_dict(suggested_size)

            # 데이터 따로 저장하기
            clothes_dict = single_clothes_dict.copy()
            clothes_dict.update(same_clothes_dict)
            clothes_dict.pop('same_photo', None)
            SingleDataList.objects.create(suggested_size=suggested_size,
                                          clothes_dict=clothes_dict,
                                          single_person_dict=single_person_dict,)

            return render(request, 'fitterKakao/single/single_result.html', {'types': kinds,
                                                                             'single_clothes_dict': single_clothes_dict,
                                                                      'clothes_link' : clothes_link,
                                                                      'clothes_nick': clothes_nick,
                                                                      'sex': user_sex,
                                                                      'height': user_height/10,
                                                                      'suggest_size': suggested_size, })

    else:
        # 이전에 들어온 쇼핑몰 같은게 있으면 url 설정하기
        referer = request.META['HTTP_REFERER'] if 'HTTP_REFERER' in request.META else ''

        same_initial, clothes_initial = is_from_other(request.GET.dict(), kinds, referer)

        person_form = PersonForm()
        same_clothes_form = SameClothesForm(initial=same_initial)

        if kinds == 'top':
            clothes_form = TopClothesForm(initial=clothes_initial)
        elif kinds == 'bot':
            clothes_form = BottomClothesForm(initial=clothes_initial)

    return render(request, 'fitterKakao/single/single_post_body.html', {'types': kinds,
                                                            'person_form': person_form,
                                                            'clothes_form': clothes_form,
                                                            'same_clothes_form': same_clothes_form, })


def single_post_between(request, kinds):
    if request.method == "POST": #이미 보낸거라면
        same_clothes_form = SameClothesForm(request.POST)
        if kinds == 'top':
            clothes_form = TopClothesForm(request.POST)
        elif kinds == 'bot':
            clothes_form = BottomClothesForm(request.POST)

        if clothes_form.is_valid() and same_clothes_form.is_valid(): # 저장된 form 형식이 잘 맞는지
            single_clothes_dict = clothes_form.cleaned_data
            same_clothes_dict = same_clothes_form.cleaned_data
            clothes_nick = same_clothes_dict['same_nick']
            clothes_link = same_clothes_dict['same_url']

            # 데이터 따로 저장하기
            clothes_dict = single_clothes_dict.copy()
            clothes_dict.update(same_clothes_dict)
            clothes_dict.pop('same_photo', None)
            SingleDataList.objects.create(clothes_dict=clothes_dict)

            return render(request, 'fitterKakao/single/single_result.html', {'types': kinds,
                                                                      'single_clothes_dict': single_clothes_dict,
                                                                      'clothes_link' : clothes_link,
                                                                      'clothes_nick': clothes_nick,
                                                                       })

    else:
        same_clothes_form = SameClothesForm()
        if kinds == 'top':
            clothes_form = TopClothesForm()
            criteria_form = CriteriaTopForm()
        elif kinds == 'bot':
            clothes_form = BottomClothesForm()
            criteria_form = CriteriaBottomForm()

    return render(request, 'fitterKakao/single/single_post_between.html', {'types': kinds,
                                                                           'criteria_form': criteria_form,
                                                                           'clothes_form': clothes_form,
                                                                           'same_clothes_form': same_clothes_form, })

